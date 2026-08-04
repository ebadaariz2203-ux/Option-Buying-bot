from execution.execution_engine import execute_trade

trade = execute_trade(
    entry_price=100,
    exit_price=110,
    signal="BUY CALL",
    quantity=75
)

print(trade)