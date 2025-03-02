import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import os
from dotenv import load_dotenv
from web import open_web

load_dotenv()

bot_token = os.getenv("BOT_TOKEN")

intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")


@bot.slash_command(name="reload", description="Reload all cogs")
async def reload(interaction: Interaction):
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.reload_extension(f"cogs.{filename[:-3]}")
    await interaction.response.send_message("reloaded all commands")

open_web()  # this function is for hosting on Koyeb

bot.run(bot_token)
