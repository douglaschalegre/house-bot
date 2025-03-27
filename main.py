import discord
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

# Define intents
intents = discord.Intents.default()
intents.messages = True  # Enable reading messages if your bot needs this
intents.message_content = True  # Required for reading message content

# Discord bot setup
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")  # Remove default help command

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
    sheet = get_sheet(month=month, year=year)
    if sheet is None:
        raise Exception(f"Spreadsheet 'Expenses {month}/{year}' not found.")


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
    data_range = sheet.get("M10:O17")  # Fetches all required cells in one API call
    data = [{"name": row[0], "value": row[1], "type": row[2]} for row in data_range]
    for row in data:
        name = row.get("name")
        value = row.get("value")
        value_type = row.get("type")
        contributions += f"{name:<20} {value:<10} {value_type:<15}\n"
    return contributions


@bot.event
async def on_message(message):
    if message.channel.id == 1328396042689052682 and not (
        message.content.startswith("!") or message.content.startswith("[ ! ]")
    ):  # Replace with your specific channel ID
        items = message.content.split("\n")
        for item in items:
            shopping_list.append(item)
            print(f"{item} added to shopping list")
    await bot.process_commands(message)


@bot.command()
async def lista(ctx):
    if shopping_list:
        formatted_list = "\n".join(f"- {item}" for item in shopping_list)
        await ctx.send(f"[ ! ] Shopping List:\n```\n{formatted_list}\n```")
    else:
        await ctx.send("[ ! ] The shopping list is currently empty.")


@bot.command()
async def ordenar(ctx):
    """
    Ordena a lista de compras usando o GPT-4
    """
    if not shopping_list:
        await ctx.send("[ ! ] The shopping list is currently empty.")
        return

    try:
        # Create the prompt for GPT-4
        items = "\n".join(shopping_list)
        prompt = f"""Por favor, organize esta lista de compras de forma lógica, agrupando itens similares.
        Considere categorias como hortifruti, laticínios, carnes, produtos de despensa, etc.
        Para cada item, adicione um marcador (-) e mantenha os nomes originais dos itens.
        Aqui está a lista:
        {items}"""

        # Make the API request using the new OpenAI client syntax
        response = await asyncio.to_thread(
            openai.chat.completions.create,  # Updated API endpoint
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

        # Extract the sorted list from the response (new response format)
        sorted_list = response.choices[0].message.content.strip()

        await ctx.send(f"[ ! ] Sorted Shopping List:\n```\n{sorted_list}\n```")
    except Exception as e:
        await ctx.send(f"[ ! ] An error occurred while sorting the list: {str(e)}")


@bot.command(aliases=["limpar"])
async def zerar(ctx):
    shopping_list.clear()
    await ctx.send("[ ! ] The shopping list has been cleared.")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    scheduler.start()


@bot.command()
async def dindin(ctx):
    current_date = datetime.now()
    month = current_date.strftime("%m")
    year = current_date.strftime("%y")
    try:
        sheet = get_sheet(month=month, year=year)
        if sheet is None:
            await ctx.send(f"Sheet for {month}/{year} not found.")
            return
        table = get_house_finance_data(sheet=sheet, month=month, year=year)
        await ctx.send(f"```\n{table}\n```")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command()
async def historico(ctx, month: str, year: str):
    """
    Query historical sheets using month and year
    Usage: !historico MM YY
    Example: !historico 03 24
    """
    try:
        # Validate month and year format
        if not (len(month) == 2 and len(year) == 2):
            await ctx.send(
                "Please provide month and year in MM YY format (e.g., 03 24)"
            )
            return

        sheet = get_sheet(month=month, year=year)
        if sheet is None:
            await ctx.send(f"Sheet for {month}/{year} not found.")
            return
        table = get_house_finance_data(sheet=sheet, month=month, year=year)
        await ctx.send(f"```\n{table}\n```")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command()
async def detalhado(ctx):
    current_date = datetime.now()
    month = current_date.strftime("%m")
    year = current_date.strftime("%y")
    try:
        sheet = get_sheet(month=month, year=year)
        if sheet is None:
            await ctx.send(f"Sheet for {month}/{year} not found.")
            return
        table = get_detailed_expenses(sheet=sheet, month=month, year=year)
        await ctx.send(f"```\n{table}\n```")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


async def send_message(channel_id: int, sheet, month, year):
    channel = bot.get_channel(channel_id)
    table = get_house_finance_data(sheet=sheet, month=month, year=year)
    await channel.send(f"```\n{table}\n```")


@scheduler.scheduled_job(CronTrigger(day="*"))  # Check every day at 0:00 AM
async def send_month_finance_data():
    current_date = datetime.now()
    month = current_date.strftime("%m")
    year = current_date.strftime("%y")
    sheet = await fetch_sheet(month=month, year=year)
    # Check if today is the 5th business day
    if is_today_fifth_business_day():
        await send_message(
            sheet=sheet, channel_id=1328396082375295078, month=month, year=year
        )
    else:
        print("No need to send monthly finance report today")


@bot.command()
async def help(ctx):
    """
    Shows all available commands and how to use them
    """
    help_text = """
**Available Commands:**

`!dindin`
Shows the current month's financial summary including salaries and contributions.

`!detalhado`
Shows a detailed view of the current month's finances, including all expenses.

`!historico MM YY`
Shows financial data for a specific month and year.
Example: `!historico 03 24` (for March 2024)

**Shopping List Features:**
- Add items by typing them in the shopping list channel
- Each line will be treated as a separate item
- Commands starting with '!' or '[ ! ]' will be ignored

`!lista`
Shows the current shopping list.

`!zerar` or `!limpar`
Clears the shopping list.

`!ordenar`
Organizes the shopping list using GPT-4.
"""
    await ctx.send(help_text)


# Run the bot
bot.run(DISCORD_TOKEN)
