import random


def simulate_price(current_price):
    """
    Simulate option premium movement.
    """

    move = random.uniform(-5, 5)

    new_price = round(current_price + move, 2)

    return new_price


if __name__ == "__main__":

    price = 180

    for i in range(10):

        price = simulate_price(price)

        print(price)