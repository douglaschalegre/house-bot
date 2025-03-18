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

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
scheduler = AsyncIOScheduler()

# Define intents
intents = discord.Intents.default()
intents.messages = True  # Enable reading messages if your bot needs this
intents.message_content = True  # Required for reading message content

# Discord bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

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


def get_house_finance_data(sheet) -> str:
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
    table = f"{'Name':<10} {'Salary':<10} {'Percent':<10} {'Contribution':<15}\n"
    table += "-" * 45 + "\n"
    for row in data:
        table += f"{row[0]:<10} {row[1]:<10} {row[2]:<10} {row[3]:<15}\n"

    return table


def get_detailed_expenses(sheet) -> str:
    contributions = get_house_finance_data(sheet=sheet)
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
        table = get_house_finance_data(sheet=get_sheet(month=month, year=year))
        await ctx.send(f"```\n{table}\n```")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command()
async def detalhado(ctx):
    current_date = datetime.now()
    month = current_date.strftime("%m")
    year = current_date.strftime("%y")
    try:
        table = get_detailed_expenses(sheet=get_sheet(month=month, year=year))
        await ctx.send(f"```\n{table}\n```")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


async def send_message(channel_id: int, sheet):
    channel = bot.get_channel(channel_id)
    table = get_house_finance_data(sheet=sheet)
    await channel.send(f"```\n{table}\n```")


@scheduler.scheduled_job(CronTrigger(day="*"))  # Check every day at 0:00 AM
async def send_month_finance_data():
    current_date = datetime.now()
    month = current_date.strftime("%m")
    year = current_date.strftime("%y")
    sheet = await fetch_sheet(month=month, year=year)
    # Check if today is the 5th business day
    if is_today_fifth_business_day():
        await send_message(sheet=sheet, channel_id=1328396082375295078)
    else:
        print("No need to send monthly finance report today")


# Run the bot
bot.run(DISCORD_TOKEN)
