import json
import os


FEATURE_FILE = "docs/features.json"


def show_features():

    if not os.path.exists(FEATURE_FILE):

        print("\nfeatures.json not found.")

        return

    with open(FEATURE_FILE, "r") as file:

        data = json.load(file)

    print("\n========== BOT FEATURES ==========\n")

    print(f"Project      : {data['project']}")
    print(f"Version      : {data['version']}")
    print(f"Current Day  : {data['current_day']}")

    print()

    print("Implemented Features:\n")

    for feature in data["features"]:

        # FIX: was print(f"✓ {feature}") — the checkmark character
        # caused UnicodeEncodeError (crash) under cp1252, and even
        # after switching to UTF-8, rendered as garbled mojibake
        # ("Γ¥î" style) depending on the Windows console's codepage
        # and font settings. Plain ASCII avoids this entirely,
        # regardless of console/terminal configuration.
        print(f"[OK] {feature}")

    print()

    print(f"Total Features : {len(data['features'])}")

    print("==================================")


def register_feature(feature_name):

    if not os.path.exists(FEATURE_FILE):
        return

    with open(FEATURE_FILE, "r") as file:
        data = json.load(file)

    if feature_name in data["features"]:

        print(f"{feature_name} already exists.")

        return

    data["features"].append(feature_name)

    with open(FEATURE_FILE, "w") as file:

        json.dump(
            data,
            file,
            indent=4
        )

    print(f"{feature_name} added successfully.")
