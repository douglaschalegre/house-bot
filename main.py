import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from app.util import is_today_fifth_business_day
import os
from dotenv import load_dotenv
import openai
import asyncio

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

scheduler = AsyncIOScheduler()
is_scheduler_started = False
is_slash_synced = False

# Define intents
intents = discord.Intents.default()
intents.messages = True  # Enable reading messages if your bot needs this
intents.message_content = True  # Required for reading message content

# Discord bot setup
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

SHOPPING_CHANNEL_ID = 1328396042689052682
FINANCE_CHANNEL_ID = 1328396082375295078

# Google Sheets setup
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)
client = gspread.authorize(credentials)

shopping_list = []


def get_sheet(month, year):
    sheet = f"Expenses {month}/{year}"
    print(sheet)
    try:
        return client.open(sheet).sheet1
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Spreadsheet '{sheet}' not found.")
        return None


# Define an async function to get the sheet using asyncio.to_thread
async def fetch_sheet(month, year):
    sheet = await asyncio.to_thread(get_sheet, month, year)
    if sheet is None:
        raise Exception(f"Spreadsheet 'Expenses {month}/{year}' not found.")
    return sheet


def get_house_finance_data(sheet, month, year) -> str:
    # Get data from the Google Sheet
    values = sheet.get("M6:O8")  # This fetches all necessary values in one go

    # Unpack the values from the fetched data
    (salario_douglas, percent_douglas, contri_douglas) = values[0]
    (salario_luana, percent_luana, contri_luana) = values[1]
    (salario_total, percent_total, contri_total) = values[2]

    # Organize the data
    data = [
        ("Douglas", salario_douglas, percent_douglas, contri_douglas),
        ("Luana", salario_luana, percent_luana, contri_luana),
        ("Total", salario_total, percent_total, contri_total),
    ]

    # Format as a table
    table = f"Sheet: Expenses {month}/{year}\n"
    table += f"{'Name':<10} {'Salary':<10} {'Percent':<10} {'Contribution':<15}\n"
    table += "-" * 45 + "\n"
    for row in data:
        table += f"{row[0]:<10} {row[1]:<10} {row[2]:<10} {row[3]:<15}\n"

    return table


def get_detailed_expenses(sheet, month, year) -> str:
    contributions = get_house_finance_data(sheet=sheet, month=month, year=year)
    contributions += "-" * 45 + "\n"
    data_range = sheet.get("M10:O22")  # Fetches all required cells in one API call
    data = [{"name": row[0], "value": row[1], "type": row[2]} for row in data_range]
    for row in data:
        name = row.get("name")
        value = row.get("value")
        value_type = row.get("type")
        contributions += f"{name:<20} {value:<10} {value_type:<15}\n"
    return contributions


def current_month_year():
    current_date = datetime.now()
    month = current_date.strftime("%m")
    year = current_date.strftime("%y")
    return month, year


async def build_finance_response(month, year, detailed=False):
    try:
        sheet = await asyncio.to_thread(get_sheet, month, year)
        if sheet is None:
            return f"Sheet for {month}/{year} not found."
        if detailed:
            table = await asyncio.to_thread(get_detailed_expenses, sheet, month, year)
        else:
            table = await asyncio.to_thread(get_house_finance_data, sheet, month, year)
        return f"```\n{table}\n```"
    except Exception as e:
        return f"An error occurred: {e}"


async def sort_shopping_items():
    items = "\n".join(shopping_list)
    prompt = f"""Por favor, organize esta lista de compras de forma lógica, agrupando itens similares.
    Considere categorias como hortifruti, laticínios, carnes, produtos de despensa, etc.
    Para cada item, adicione um marcador (-) e mantenha os nomes originais dos itens.
    Aqui está a lista:
    {items}"""

    response = await asyncio.to_thread(
        openai.chat.completions.create,
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that organizes shopping lists into logical categories.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def build_help_text():
    return """
**Available Slash Commands:**

`/dindin`
Shows the current month's financial summary including salaries and contributions.

`/detalhado`
Shows a detailed view of the current month's finances, including all expenses.

`/historico month:<1-12> year:<0-99>`
Shows financial data for a specific month and year.
Example: `/historico month:3 year:24` (for March 2024)

**Shopping List Features:**
- Add items by typing them in the shopping list channel
- Each line will be treated as a separate item
- Bot messages are ignored

`/lista`
Shows the current shopping list.

`/zerar`
Clears the shopping list.

`/ordenar`
Organizes the shopping list using GPT-4.

`/help`
Shows this help message.
"""


async def resolve_sync_guild():
    channel = bot.get_channel(SHOPPING_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(SHOPPING_CHANNEL_ID)
        except discord.DiscordException as e:
            print(f"Unable to fetch shopping channel for slash sync: {e}")
            return None

    guild = getattr(channel, "guild", None)
    if guild is None:
        print("Unable to resolve guild from shopping channel for slash sync.")
        return None
    return guild


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == SHOPPING_CHANNEL_ID and not (
        message.content.startswith("!") or message.content.startswith("[ ! ]")
    ):
        items = [item.strip() for item in message.content.split("\n") if item.strip()]
        for item in items:
            shopping_list.append(item)
            print(f"{item} added to shopping list")


@bot.tree.command(name="lista", description="Shows the current shopping list.")
async def lista_command(interaction: discord.Interaction):
    if shopping_list:
        formatted_list = "\n".join(f"- {item}" for item in shopping_list)
        await interaction.response.send_message(
            f"[ ! ] Shopping List:\n```\n{formatted_list}\n```"
        )
    else:
        await interaction.response.send_message(
            "[ ! ] The shopping list is currently empty."
        )


@bot.tree.command(name="ordenar", description="Organizes the shopping list using GPT-4.")
async def ordenar_command(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    if not shopping_list:
        await interaction.followup.send("[ ! ] The shopping list is currently empty.")
        return

    try:
        sorted_list = await sort_shopping_items()
        await interaction.followup.send(
            f"[ ! ] Sorted Shopping List:\n```\n{sorted_list}\n```"
        )
    except Exception as e:
        await interaction.followup.send(
            f"[ ! ] An error occurred while sorting the list: {str(e)}"
        )


@bot.event
async def on_ready():
    global is_scheduler_started, is_slash_synced

    print(f"Logged in as {bot.user.name}")

    if not is_scheduler_started:
        scheduler.start()
        is_scheduler_started = True
        print("Scheduler started.")

    if not is_slash_synced:
        guild = await resolve_sync_guild()
        if guild is None:
            print("Slash command sync skipped; will retry on next ready event.")
            return

        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        is_slash_synced = True
        print(f"Synced {len(synced)} slash commands to guild {guild.id}.")


@bot.tree.command(
    name="dindin",
    description="Shows the current month's financial summary including salaries and contributions.",
)
async def dindin_command(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    month, year = current_month_year()
    message = await build_finance_response(month=month, year=year)
    await interaction.followup.send(message)


@bot.tree.command(
    name="historico",
    description="Shows financial data for a specific month and year.",
)
@app_commands.describe(month="Month number from 1 to 12", year="Two-digit year (0-99)")
async def historico_command(
    interaction: discord.Interaction,
    month: app_commands.Range[int, 1, 12],
    year: app_commands.Range[int, 0, 99],
):
    await interaction.response.defer(thinking=True)
    month_str = f"{month:02d}"
    year_str = f"{year:02d}"
    message = await build_finance_response(month=month_str, year=year_str)
    await interaction.followup.send(message)


@bot.tree.command(
    name="detalhado",
    description="Shows a detailed view of the current month's finances, including all expenses.",
)
async def detalhado_command(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    month, year = current_month_year()
    message = await build_finance_response(month=month, year=year, detailed=True)
    await interaction.followup.send(message)


async def send_message(channel_id: int, sheet, month, year):
    channel = bot.get_channel(channel_id)
    if channel is None:
        channel = await bot.fetch_channel(channel_id)
    table = get_house_finance_data(sheet=sheet, month=month, year=year)
    await channel.send(f"```\n{table}\n```")


@scheduler.scheduled_job(CronTrigger(day="*"))  # Check every day at 0:00 AM
async def send_month_finance_data():
    month, year = current_month_year()

    try:
        sheet = await fetch_sheet(month=month, year=year)
    except Exception as e:
        print(f"Failed to get sheet for scheduled message: {e}")
        return

    # Check if today is the 5th business day
    if is_today_fifth_business_day():
        await send_message(sheet=sheet, channel_id=FINANCE_CHANNEL_ID, month=month, year=year)
    else:
        print("No need to send monthly finance report today")


@bot.tree.command(name="zerar", description="Clears the shopping list.")
async def zerar_command(interaction: discord.Interaction):
    shopping_list.clear()
    await interaction.response.send_message("[ ! ] The shopping list has been cleared.")


@bot.tree.command(name="help", description="Shows all available slash commands.")
async def help_command(interaction: discord.Interaction):
    await interaction.response.send_message(build_help_text())


# Run the bot
bot.run(DISCORD_TOKEN)
