import os
import dotenv
import logging

from piepy.setup import bot, setup, log_handler

if __name__ == "__main__":
    dotenv.load_dotenv()

    setup()
    logging.info("봇을 시작합니다")
    logging.info("심심하다야")

    bot.run(
        os.getenv("BOT_TOKEN"),
        log_handler=log_handler,
        log_level=logging.INFO,
        root_logger=True
    )