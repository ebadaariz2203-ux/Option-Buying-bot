from config import *
from core.bot import TradingBot


def main():

    print("=" * 50)
    print(BOT_NAME)
    print("Version :", VERSION)
    print("Paper Trading :", PAPER_TRADING)
    print("=" * 50)

    bot = TradingBot()
    bot.run()


if __name__ == "__main__":
    main()
