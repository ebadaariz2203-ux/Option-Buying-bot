"""
Dynamic Option Pricing

Responsible for:
- Reading option premium
- Validating premium
- Returning entry price
"""


class DynamicOptionPricing:

    @staticmethod
    def get_entry_price(selected_strike):

        if selected_strike is None:
            return None

        premium = selected_strike.get("LTP")

        if premium is None:
            return None

        if premium <= 0:
            return None

        return round(float(premium), 2)