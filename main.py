from config import *
from logger.logger import logger
from risk.risk_manager import calculate_pnl
from paper_trade.paper_trade import (
    
    execute_paper_trade,
    save_trade,

)

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
    signal = bot.generate_trading_signal(data)
   
    # Risk Management
    if signal != "NO TRADE":

        trade, position, validation = bot.manage_risk(signal, data)

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

            paper_trade = bot.execute_trade(signal, trade)

            message = f"""
    📢 OPTION BUYING BOT

    Signal : {signal}

    Entry : {trade['Entry']}
    Stop Loss : {trade['StopLoss']}
    Target : {trade['Target']}

    Status : OPEN
    """

            bot.send_notification(message)
            print("\n========== PAPER TRADE ==========")
            print(f"Time        : {paper_trade['Time']}")
            print(f"Signal      : {paper_trade['Signal']}")
            print(f"Entry       : {paper_trade['Entry']}")
            print(f"Stop Loss   : {paper_trade['StopLoss']}")
            print(f"Target      : {paper_trade['Target']}")
            print(f"Status      : {paper_trade['Status']}")
            print("=================================")

                      
        else:

            print("\nTrade Rejected.")
            print(validation["Reason"])

            # Trade Status
            current_price = 190.00
            status = bot.get_trade_status(current_price, trade)

            trade_status_message = f"""
    📊 TRADE UPDATE

    Signal : {signal}

    Current Price : {current_price}

    Status : {status}
    """

            bot.send_notification(trade_status_message)

            print("\n========== TRADE STATUS ==========")
            print(f"Current Price : {current_price}")
            print(f"Trade Status  : {status}")
            print("==================================")

            # Trade Result (PnL)
            exit_price = 210.00

            result = calculate_pnl(trade["Entry"], exit_price)

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

            bot.send_notification(result_message)
            print("\nTrade Saved Successfully.")

    else:
        print("\nNo Trade Found.")

if __name__ == "__main__":
    main()
