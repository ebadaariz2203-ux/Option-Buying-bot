import yfinance as yf


ticker = yf.Ticker("^NSEI")

print("\n========== NIFTY ==========")

print("Spot Price:")

try:
    history = ticker.history(period="1d")

    print(history["Close"].tail())

except Exception as e:

    print("Spot Price Error:", e)


print("\n========== OPTION EXPIRATIONS ==========")

try:

    expirations = ticker.options

    print(expirations)

except Exception as e:

    print("Option Chain Error:", e)