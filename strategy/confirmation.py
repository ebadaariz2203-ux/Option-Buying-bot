"""
Option Chain Confirmations
"""


def bullish_confirmation(pcr):

    if pcr is None:
        return True

    return pcr > 1


def bearish_confirmation(pcr):

    if pcr is None:
        return True

    return pcr < 1