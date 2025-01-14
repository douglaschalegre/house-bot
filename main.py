import discord
from discord.ext import commands
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from app.util import is_today_fifth_business_day
import os

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

# Get the current month and year
current_date = datetime.now()
month = current_date.strftime(
    "%m"
)  # Format as two-digit month (e.g., "01" for January)
year = current_date.strftime("%y")  # Format as two-digit year (e.g., "25" for 2025)
print(month, year)
# Dynamically generate the sheet name
sheet = client.open(f"Expenses {month}/{year}").sheet1


def get_house_finance_data(sheet) -> str:
    # Get data from the Google Sheet
    salario_douglas, salario_luana, salario_total = (
        sheet.cell(6, 13).value,
        sheet.cell(7, 13).value,
        sheet.cell(8, 13).value,
    )
    percent_douglas, percent_luana, percent_total = (
        sheet.cell(6, 14).value,
        sheet.cell(7, 14).value,
        sheet.cell(8, 14).value,
    )
    contri_douglas, contri_luana, contri_total = (
        sheet.cell(6, 15).value,
        sheet.cell(7, 15).value,
        sheet.cell(8, 15).value,
    )
    # Convert all values to strings for display
    data = [
        ("Douglas", salario_douglas, percent_douglas, contri_douglas),
        ("Luana", salario_luana, percent_luana, contri_luana),
        ("Total", salario_total, percent_total, contri_total),
    ]

    # Format as a table
    table = f"{'Name':<10} {'Salary':<15} {'Percent':<10} {'Contribution':<15}\n"
    table += "-" * 50 + "\n"
    for row in data:
        table += f"{row[0]:<10} {row[1]:<15} {row[2]:<10} {row[3]:<15}\n"

    return table


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    scheduler.start()


@bot.command()
async def dindin(ctx):
    try:
        table = get_house_finance_data(sheet=sheet)
        await ctx.send(f"```\n{table}\n```")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


async def send_message(channel_id: int, sheet):
    channel = bot.get_channel(channel_id)
    table = get_house_finance_data(sheet=sheet)
    await channel.send(f"```\n{table}\n```")


@scheduler.scheduled_job(CronTrigger(minute="55"))  # Check every day at 0:00 AM
async def send_month_finance_data():
    current_date = datetime.now()
    month = current_date.strftime("%m")
    year = current_date.strftime("%y")
    sheet = client.open(f"Expenses {month}/{year}").sheet1
    # Check if today is the 5th business day
    if is_today_fifth_business_day():
        await send_message(sheet=sheet, channel_id=1328396082375295078)
    else:
        print("No need to send monthly finance report today")


# Run the bot
bot.run(DISCORD_TOKEN)
