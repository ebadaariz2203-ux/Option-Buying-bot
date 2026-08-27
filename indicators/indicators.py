import pandas as pd
import numpy as np


def wilder_smoothing(series, period):
    """
    NEW FUNCTION — Wilder's smoothing (a.k.a. Running Moving Average /
    RMA), as defined by J. Welles Wilder Jr. (who invented RSI, ADX,
    and ATR — all three are DEFINED using this exact smoothing, not a
    simple rolling average).

    Recursive formula:
        smoothed[0] = value[0]
        smoothed[t] = smoothed[t-1] + (value[t] - smoothed[t-1]) / period

    This is mathematically identical to an exponential moving average
    with alpha = 1/period, computed non-adjusted (recursively) — which
    is exactly what pandas' ewm(alpha=1/period, adjust=False) computes.
    This is the same method used by TradingView and most brokers, so
    RSI/ADX/ATR values calculated this way will match what you see on
    a live chart much more closely than a plain rolling mean does.
    """

    return series.ewm(alpha=1 / period, adjust=False).mean()


def calculate_ema(data, period=20):

    data[f"EMA_{period}"] = data["Close"].ewm(
        span=period,
        adjust=False
    ).mean()

    return data


def calculate_rsi(data, period=14):
    """
    FIX: now uses Wilder's smoothing (see wilder_smoothing() above)
    for the average gain/loss, instead of a plain rolling mean. This
    is the original/standard RSI definition and matches TradingView
    and broker platforms. Plain-rolling-mean RSI (the old version)
    reacts faster to recent moves and can diverge noticeably from the
    "real" RSI you'd see on a chart, especially in the first several
    dozen candles and around sharp moves.

    NOTE: Because this changes the actual RSI values produced, your
    existing RSI thresholds (e.g. RSI > 55 in strategy/filters.py)
    are now being compared against a smoother, more standard RSI.
    Values will generally be less spiky than before — worth watching
    for a few sessions before deciding if thresholds need adjusting.
    """

    delta = data["Close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = wilder_smoothing(gain, period)
    avg_loss = wilder_smoothing(loss, period)

    rs = avg_gain / avg_loss

    data["RSI"] = 100 - (100 / (1 + rs))

    return data


def calculate_adx(data, period=14):
    """
    Calculate Average Directional Index (ADX)

    Required Columns:
    High
    Low
    Close

    FIX: now uses Wilder's smoothing (see wilder_smoothing() above)
    for +DM, -DM, True Range, and the final DX->ADX step, instead of
    a plain rolling mean at each stage. ADX is Wilder's own indicator
    and is DEFINED using this smoothing throughout — the old
    plain-rolling-mean version was a simplified approximation, not
    "real" ADX, and would read noticeably differently from what
    TradingView/your broker shows for the same candles.

    NOTE: This changes the actual ADX values. Your ADX_STRONG_TREND /
    ADX_WEAK_TREND thresholds (config/settings.py) are now being
    compared against standard Wilder ADX. Wilder ADX tends to be
    smoother and slower to rise/fall than the old version — worth
    watching a few sessions to see if CHOPPY/TRENDING classifications
    still feel right before adjusting thresholds.
    """

    df = data.copy()

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    # Directional Movement
    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm = plus_dm.where(
        (plus_dm > minus_dm) & (plus_dm > 0),
        0
    )

    minus_dm = minus_dm.where(
        (minus_dm > plus_dm) & (minus_dm > 0),
        0
    )

    # True Range
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = wilder_smoothing(tr, period)

    plus_di = 100 * (
        wilder_smoothing(plus_dm, period) / atr
    )
    minus_di = 100 * (
        wilder_smoothing(minus_dm, period) / atr
    )

    di_sum = plus_di + minus_di

    # FIX: when plus_di + minus_di == 0 (both flat), the original
    # division produced 0/0 -> NaN/inf. Replace 0 with NaN in the
    # denominator so those rows resolve to NaN cleanly instead of a
    # runtime warning / inf propagating into downstream comparisons
    # (e.g. "adx >= ADX_STRONG_TREND" against a NaN silently
    # evaluates False, which is safe, but inf could behave
    # unpredictably).
    dx = (
        (plus_di - minus_di).abs()
        / di_sum.replace(0, float("nan"))
    ) * 100

    adx = wilder_smoothing(dx, period)

    data["ADX"] = adx

    return data


def calculate_vwap(data):
    """
    Calculate session VWAP using valid volume.

    VWAP = cumulative(Typical Price x Volume)
           / cumulative(Volume)

    FIX: previously used a single running cumsum() across the ENTIRE
    passed DataFrame. Callers like kite_provider.get_nifty_futures_data()
    fetch 2 days of candles at a time (days=2) — with the old code,
    day 2's VWAP kept accumulating on top of day 1's totals instead of
    resetting at the start of each new trading session. This produced
    an incorrect VWAP value that fed directly into the VWAP
    confirmation filter (strategy/vwap_filter.py), potentially
    rejecting or accepting signals based on a distorted number.

    Now the cumulative sums reset at the start of each calendar date
    (each trading session), matching how VWAP is defined/used in
    practice.
    """

    data = data.copy()

    typical_price = (
        data["High"]
        + data["Low"]
        + data["Close"]
    ) / 3

    volume = pd.to_numeric(
        data["Volume"],
        errors="coerce"
    ).fillna(0)

    tp_volume = typical_price * volume

    # Group by calendar date (session) so cumulative sums reset each
    # trading day instead of accumulating across multiple days.
    session_date = data.index.date

    cumulative_volume = volume.groupby(session_date).cumsum()
    cumulative_tp_volume = tp_volume.groupby(session_date).cumsum()

    data["VWAP"] = (
        cumulative_tp_volume /
        cumulative_volume.replace(0, float("nan"))
    )

    return data


def calculate_volume_average(data, period=20):

    data["Volume_Avg"] = data["Volume"].rolling(period).mean()

    return data


def calculate_atr(data, period=14):
    """
    FIX: now uses Wilder's smoothing (see wilder_smoothing() above)
    instead of a plain rolling mean. ATR is Wilder's own indicator and
    is DEFINED this way — this is what TradingView/brokers show as
    "ATR".

    IMPORTANT: This ATR feeds directly into your Stop Loss / Target
    sizing (risk/risk_manager.py -> calculate_trade()) via
    convert_atr_to_option_premium(). Wilder-smoothed ATR is generally
    a bit smoother and can differ in magnitude from the old
    plain-average ATR (usually similar, sometimes noticeably
    different right after a volatile candle, since plain rolling mean
    drops old values abruptly while Wilder's fades them out
    gradually). This means your actual Stop Loss / Target distances in
    rupees will shift slightly starting from your next trade. Nothing
    to configure — just something to notice in the first few trades
    after this change.
    """

    high = data["High"]
    low = data["Low"]
    close = data["Close"]

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    true_range = tr1.combine(tr2, max)
    true_range = true_range.combine(tr3, max)

    data["ATR"] = wilder_smoothing(true_range, period)

    return data


def get_trend(data):
    """
    Determine market trend using EMA 20 and EMA 50.
    Returns:
        UPTREND
        DOWNTREND
        SIDEWAYS
    """

    # Make sure EMAs exist
    if "EMA_20" not in data.columns:
        data = calculate_ema(data, 20)

    if "EMA_50" not in data.columns:
        data = calculate_ema(data, 50)

    ema20 = data["EMA_20"].iloc[-1]
    ema50 = data["EMA_50"].iloc[-1]

    if ema20 > ema50:
        return "UPTREND"
    elif ema20 < ema50:
        return "DOWNTREND"
    else:
        return "SIDEWAYS"
