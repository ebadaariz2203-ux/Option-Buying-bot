from config.settings import CAPITAL, RISK_PER_TRADE, LOT_SIZE


def calculate_position_size(entry_price, stop_loss):

    max_loss = CAPITAL * (RISK_PER_TRADE / 100)

    risk_per_lot = abs(entry_price - stop_loss) * LOT_SIZE

    # FIX: risk_per_lot can be exactly 0 when a degenerate ATR/stop-loss
    # collapses onto entry price (e.g. index ATR rounds to 0.00) -- this
    # used to divide by zero here and crash the whole bot process. It
    # also used to force a minimum of 1 lot via max(1, ...) even when
    # that single lot's own risk already exceeded max_loss, silently
    # letting a trade risk more than the configured RISK_PER_TRADE with
    # nothing to catch it. Both cases now size to 0 lots instead --
    # validate_trade()'s existing "Lots < 1" check already rejects a
    # 0-lot trade, so this fails safe with no crash and no risk-cap
    # breach.
    if risk_per_lot <= 0:
        lots = 0
    else:
        lots = int(max_loss // risk_per_lot)

    required_capital = round(entry_price * LOT_SIZE * lots, 2)

    return {

        "Capital": CAPITAL,

        "RiskPercent": RISK_PER_TRADE,

        "MaxLoss": round(max_loss, 2),

        "RiskPerLot": round(risk_per_lot, 2),

        "Lots": lots,

        "Quantity": lots * LOT_SIZE,

        "EnoughCapital": required_capital <= CAPITAL,

        "RequiredCapital": required_capital,

    }