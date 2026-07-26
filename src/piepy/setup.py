import importlib
import logging
import shutil
import sys
import os
import time

import pymysql

import discord
from discord.ext import commands
from discord.ext.commands import ExtensionAlreadyLoaded

from .extensions import preload_modules, extensions

# from piepy.cli import CLIRunner

intents = discord.Intents.all()
intents.message_content = True

log_handler = logging.FileHandler(filename='latest.log', encoding='utf-8', mode='w')

# cli_runner: CLIRunner = CLIRunner()
bot: commands.Bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    logging.info(f'"{bot.user}" 로 로그인 완료')

    for ext in extensions:
        logging.info(f'Loading extension: "{ext}"')
        try:
            await bot.load_extension(ext)
            logging.info(f'Done loading extension: {ext}')
        except ExtensionAlreadyLoaded:
            logging.warning(f'Extension: "{ext}" is already loaded. ignore.')

    logging.info("Done!")
    logging.info("Timings Reset")

    logging.info("명령어 동기화중...")
    await bot.tree.sync()
    logging.info("명령어 동기화 완료")


def setup():
    print("Setting up...")
    discord.utils.setup_logging()

    logging.info("Initializing temp directory...")
    try:
        shutil.rmtree("./temp")
    except FileNotFoundError: pass
    os.mkdir("temp")
    logging.info("Initialized.")

    logging.info("Checking opus...")
    if sys.platform == "darwin":
        logging.info("darwin platform detected. loading opus")
        discord.opus.load_opus("/opt/homebrew/lib/libopus.dylib")
        logging.info("Opus loaded.")

    logging.info("Load preload packages...")
    for module in preload_modules:
        logging.info(f'Load "{module}"...')
        importlib.import_module(module)
        logging.info(f'"{module}" loaded')


    logging.info('Trying to connect to database for 60s')

    is_connected = False
    for i in range(60):
        try:
            # conn = pymysql.connect(
            #     host='db',
            #     user='root',
            #     password='root',
            #     database='piepydb'
            # )
            conn = pymysql.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DATABASE')
            )
            is_connected = True
            break
        except pymysql.err.OperationalError:
            print(f'{i}th attempt: database not ready, retrying in 1s...')
            time.sleep(1)

    if is_connected:
        logging.info('Database is ready')
    else:
        logging.error("Can't connect to database")
        raise ConnectionError("Can't connect to database")

    logging.info("Setup database engine...")
    logging.info("Init database...")
    logging.info("Database initialized.")


__all__ = [
    "bot",
    # "cli_runner",
    "log_handler",
    "setup",
]
