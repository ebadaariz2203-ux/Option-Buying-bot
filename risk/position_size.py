from config.settings import CAPITAL, RISK_PER_TRADE, LOT_SIZE


def calculate_position_size(entry_price, stop_loss):

    max_loss = CAPITAL * (RISK_PER_TRADE / 100)

    risk_per_lot = abs(entry_price - stop_loss) * LOT_SIZE

    lots = max(1, int(max_loss // risk_per_lot))

    required_capital = entry_price * LOT_SIZE * lots


    return {

        "Capital": CAPITAL,

        "RiskPercent": RISK_PER_TRADE,

        "MaxLoss": round(max_loss, 2),

        "RiskPerLot": round(risk_per_lot, 2),

        "Lots": lots,

        "Quantity": lots * LOT_SIZE,

        "EnoughCapital": required_capital <= CAPITAL,

        "RequiredCapital": round(required_capital, 2),

    }