import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import os
from dotenv import load_dotenv
from web import open_web

load_dotenv()

bot_token = os.getenv("BOT_TOKEN")
admin = os.getenv("ADMIN")

intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents, owner_id=int(admin))


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    print(f"admin: {admin}")


for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")


@bot.slash_command(name="reload", description="Reload all cogs")
@commands.is_owner()
async def reload(interaction: Interaction):
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.reload_extension(f"cogs.{filename[:-3]}")
    await interaction.response.send_message("reloaded all commands")

open_web()  # 다른 사이트 호스팅 용도, 로컬로 호스팅 시 필요없음

bot.run(bot_token)
