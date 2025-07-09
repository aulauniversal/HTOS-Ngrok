from dotenv import load_dotenv
load_dotenv()

import discord
import argparse
import threading
import os
from flask import Flask, send_from_directory
from pyngrok import ngrok

from utils.constants import bot, TOKEN
from utils.workspace import WorkspaceOpt, startup, check_version
from utils.helpers import threadButton


DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "downloads")
app = Flask(__name__)

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

def start_local_server():
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    public_url = ngrok.connect(8080, "http")
    print(f"[NGROK] Servidor público en: {public_url}")
    app.run(port=8080)

# Starting Server http
threading.Thread(target=start_local_server, daemon=True).start()


workspace_opt = WorkspaceOpt()

@bot.event
async def on_ready() -> None:
    from google_drive import checkGDrive
    startup(workspace_opt)
    await check_version()
    bot.add_view(threadButton()) # make view persistent
    checkGDrive.start() # start gd daemon
    print(
        f"Bot is ready, invite link: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot"
    )

@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    if message.content == "hello":
        await message.channel.send("hi")

    await bot.process_commands(message)

cogs_list = [
    "change",
    "convert",
    "createsave",
    "decrypt",
    "encrypt",
    "extra",
    "misc",
    "quick",
    "reregion",
    "resign",
    "sealed_key",
    "sfo",
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ignore-startup", action="store_true")
    args = parser.parse_args()
    if args.ignore_startup:
        workspace_opt.ignore_startup = True

    for cog in cogs_list:
        print(f"Loading cog: {cog}...")
        bot.load_extension(f"cogs.{cog}")
        print(f"Loaded cog: {cog}.")
    
    print("Starting bot...\n\n")
    def auto_clean_downloads(interval_minutes=60, max_age_minutes=60):
        while True:
            now = time.time()
            deleted = 0
            for filename in os.listdir(DOWNLOAD_FOLDER):
                file_path = os.path.join(DOWNLOAD_FOLDER, filename)
                if os.path.isfile(file_path):
                    file_age = (now - os.path.getmtime(file_path)) / 60  # minutos
                    if file_age > max_age_minutes:
                        try:
                            os.remove(file_path)
                            deleted += 1
                        except Exception as e:
                            print(f"[CLEANUP] No se pudo borrar {filename}: {e}")
            if deleted:
                print(f"[CLEANUP] {deleted} archivo(s) eliminados de downloads/")
            time.sleep(interval_minutes * 60)
    bot.run(TOKEN)
