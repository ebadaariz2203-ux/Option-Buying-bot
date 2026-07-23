from config import *
from logger.logger import logger

from market_data.market_data import get_nifty_data
from strategy.strategy import generate_signal
from risk.risk_manager import calculate_trade, calculate_pnl
from risk.position_size import calculate_position_size
from paper_trade.trade_validator import validate_trade

from paper_trade.paper_trade import (
    
    execute_paper_trade,
    save_trade,
    check_trade_status
)
from option_chain.option_data import get_option_chain
from telegram.telegram_bot import send_telegram_message
from core.bot import TradingBot

def main():

    print("=" * 50)
    print(BOT_NAME)
    print("Version :", VERSION)
    print("Paper Trading :", PAPER_TRADING)
    print("=" * 50)

    bot = TradingBot()
   # Download Market Data
    
    data = bot.fetch_market_data()

    # Calculate Indicators
    data = bot.calculate_indicators(data)

    # Generate Trading Signal
    option = get_option_chain()
    print("\n========== OPTION CHAIN ==========")
    print(f"PCR        : {option['PCR']}")
    print(f"Call OI    : {option['Call_OI']}")
    print(f"Put OI     : {option['Put_OI']}")
    print(f"ATM Strike : {option['ATM_Strike']}")
    print("==================================")

    signal = generate_signal(data, option)
    print(f"\nTrading Signal : {signal}")

    logger.info(f"Trading Signal : {signal}")


    # Risk Management
    if signal != "NO TRADE":

        # Temporary option premium for testing
        entry_price = 180.00
        atr = float(data.iloc[-1]["ATR"])

        trade = calculate_trade(entry_price, atr)
        position = calculate_position_size(
            trade["Entry"],
            trade["StopLoss"]
        )

        validation = validate_trade(position)

        print("\n========== TRADE DETAILS ==========")
        print(f"Entry Price : {trade['Entry']}")
        print(f"ATR         : {trade['ATR']}")
        print(f"ATR Mult.   : {trade['ATRMultiplier']}")
        print(f"RiskReward  : 1:{trade['RiskReward']}")
        print(f"Stop Loss   : {trade['StopLoss']}")
        print(f"Target      : {trade['Target']}")
        print("===================================")

        print("\n========== POSITION SIZE ==========")
        print(f"Capital      : {position['Capital']}")
        print(f"Risk %       : {position['RiskPercent']}%")
        print(f"Max Loss     : {position['MaxLoss']}")
        print(f"Risk / Lot   : {position['RiskPerLot']}")
        print(f"Lots to Buy  : {position['Lots']}")
        print("===================================")

        print("\n========== TRADE VALIDATION ==========")
        print(f"Allowed : {validation['Allowed']}")
        print(f"Reason  : {validation['Reason']}")
        print("======================================")

        if validation["Allowed"]:

            paper_trade = execute_paper_trade(signal, trade)

            message = f"""
    📢 OPTION BUYING BOT

    Signal : {signal}

    Entry : {trade['Entry']}
    Stop Loss : {trade['StopLoss']}
    Target : {trade['Target']}

    Status : OPEN
    """

            send_telegram_message(message)

            print("\n========== PAPER TRADE ==========")
            print(f"Time        : {paper_trade['Time']}")
            print(f"Signal      : {paper_trade['Signal']}")
            print(f"Entry       : {paper_trade['Entry']}")
            print(f"Stop Loss   : {paper_trade['StopLoss']}")
            print(f"Target      : {paper_trade['Target']}")
            print(f"Status      : {paper_trade['Status']}")
            print("=================================")

            # Save Trade
            save_trade(paper_trade)

        else:

            print("\nTrade Rejected.")
            print(validation["Reason"])

            # Trade Status
            current_price = 190.00

            status = check_trade_status(current_price, trade)

            trade_status_message = f"""
    📊 TRADE UPDATE

    Signal : {signal}

    Current Price : {current_price}

    Status : {status}
    """

            send_telegram_message(trade_status_message)

            print("\n========== TRADE STATUS ==========")
            print(f"Current Price : {current_price}")
            print(f"Trade Status  : {status}")
            print("==================================")

            # Trade Result (PnL)
            exit_price = 210.00

            result = calculate_pnl(entry_price, exit_price)

            print("\n========== TRADE RESULT ==========")
            print(f"Entry Price : {result['Entry']}")
            print(f"Exit Price  : {result['Exit']}")
            print(f"PnL         : {result['PnL']}")
            print(f"Return %    : {result['PnLPercent']}%")

            if result["PnL"] > 0:
                print("Status      : PROFIT")
            elif result["PnL"] < 0:
                print("Status      : LOSS")
            else:
                print("Status      : BREAKEVEN")

            print("==================================")

            result_message = f"""
    📈 TRADE CLOSED

    Entry : {result['Entry']}
    Exit : {result['Exit']}

    PnL : {result['PnL']}
    Return : {result['PnLPercent']}%

    Status : {'PROFIT' if result['PnL'] > 0 else 'LOSS'}
    """

            send_telegram_message(result_message)

            print("\nTrade Saved Successfully.")

    else:
        print("\nNo Trade Found.")

if __name__ == "__main__":
    main()
