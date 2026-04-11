from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "scotch_progression_observations.csv"


PRODUCTS = [
    {"brand": "Johnnie Walker", "expression": "Red Label", "whisky_type": "blend", "age_statement": np.nan, "pack_sizes": [750, 1000], "base_price": 255, "tier": "entry", "peat_profile": "light"},
    {"brand": "Johnnie Walker", "expression": "Black Label", "whisky_type": "blend", "age_statement": 12, "pack_sizes": [750], "base_price": 430, "tier": "core", "peat_profile": "medium"},
    {"brand": "Monkey Shoulder", "expression": "Blended Malt", "whisky_type": "blend", "age_statement": np.nan, "pack_sizes": [750], "base_price": 445, "tier": "core", "peat_profile": "medium"},
    {"brand": "Chivas Regal", "expression": "12", "whisky_type": "blend", "age_statement": 12, "pack_sizes": [750], "base_price": 470, "tier": "core", "peat_profile": "light"},
    {"brand": "Glenfiddich", "expression": "12", "whisky_type": "single_malt", "age_statement": 12, "pack_sizes": [750], "base_price": 515, "tier": "premium", "peat_profile": "light"},
    {"brand": "Glenlivet", "expression": "12", "whisky_type": "single_malt", "age_statement": 12, "pack_sizes": [750], "base_price": 565, "tier": "premium", "peat_profile": "light"},
    {"brand": "Laphroaig", "expression": "10", "whisky_type": "single_malt", "age_statement": 10, "pack_sizes": [750], "base_price": 930, "tier": "distinctive", "peat_profile": "heavy"},
    {"brand": "Lagavulin", "expression": "16", "whisky_type": "single_malt", "age_statement": 16, "pack_sizes": [750], "base_price": 1325, "tier": "distinctive", "peat_profile": "heavy"},
]


def main() -> None:
    rng = np.random.default_rng(SEED)
    product_weights = np.array([0.24, 0.15, 0.14, 0.14, 0.11, 0.09, 0.08, 0.05], dtype=float)
    product_weights = product_weights / product_weights.sum()

    store_types = ["liquor_store", "retail_chain", "premium_store"]
    store_weights = [0.47, 0.34, 0.19]
    shelf_zones = ["eye_level", "lower", "end_cap", "feature_display"]
    display_types = ["standard", "gift_section", "promo_stack"]
    city_regions = ["Sandton", "Rosebank", "Randburg", "Midrand", "Pretoria East", "East Rand"]
    occasions = [None, "quiet pour", "weekend top-up", "host gift", "braai night", "birthday run", "try something else", "last-minute dinner", "special bottle", "month-end stock-up", "corporate gift"]

    rows = []
    for _ in range(3200):
        product = PRODUCTS[int(rng.choice(len(PRODUCTS), p=product_weights))]
        store_type = str(rng.choice(store_types, p=store_weights))
        shelf_zone = str(rng.choice(shelf_zones, p=[0.30, 0.30, 0.22, 0.18]))
        display_type = str(rng.choice(display_types, p=[0.55, 0.25, 0.20]))
        pack_size_ml = int(rng.choice(product["pack_sizes"]))
        week = int(rng.integers(1, 53))
        city_region = str(rng.choice(city_regions))

        gift_box_prob = {"entry": 0.20, "core": 0.28, "premium": 0.34, "distinctive": 0.38}[product["tier"]]
        is_gift_boxed = int(rng.random() < gift_box_prob)

        purchase_type = str(
            rng.choice(
                ["self", "gift", "mixed"],
                p={
                    "entry": [0.62, 0.16, 0.22],
                    "core": [0.52, 0.20, 0.28],
                    "premium": [0.48, 0.22, 0.30],
                    "distinctive": [0.43, 0.27, 0.30],
                }[product["tier"]],
            )
        )

        stage = str(
            rng.choice(
                ["entry", "familiar", "exploratory", "preference_led"],
                p={
                    "entry": [0.48, 0.35, 0.14, 0.03],
                    "core": [0.18, 0.39, 0.31, 0.12],
                    "premium": [0.07, 0.24, 0.39, 0.30],
                    "distinctive": [0.03, 0.15, 0.36, 0.46],
                }[product["tier"]],
            )
        )

        base_price = float(product["base_price"])
        price = base_price * (1 + rng.normal(0, 0.08))
        if pack_size_ml == 1000:
            price *= 1.23
        if is_gift_boxed:
            price *= 1.05
        price = round(max(185, price), 2)

        if price <= 320:
            price_band = "budget_edge"
        elif price <= 420:
            price_band = "step_up"
        elif price <= 700:
            price_band = "premium_window"
        elif price <= 950:
            price_band = "stretch"
        else:
            price_band = "top_shelf"

        occasion = rng.choice(
            occasions,
            p=[0.24, 0.15, 0.12, 0.09, 0.08, 0.07, 0.06, 0.06, 0.06, 0.05, 0.02],
        )
        basket_role = "add_on" if rng.random() < 0.09 else "primary"
        promo_flag = int(rng.random() < {"standard": 0.14, "gift_section": 0.10, "promo_stack": 0.42}[display_type])

        repeat_base = {
            "entry": 0.18,
            "core": 0.30,
            "premium": 0.24,
            "distinctive": 0.33,
        }[product["tier"]]
        repeat_base += {"entry": -0.07, "familiar": 0.03, "exploratory": -0.02, "preference_led": 0.11}[stage]
        repeat_base += {"self": 0.06, "gift": -0.10, "mixed": -0.02}[purchase_type]
        repeat_base += {"standard": 0.03, "gift_section": -0.05, "promo_stack": -0.02}[display_type]
        repeat_base -= 0.04 if is_gift_boxed else 0.0
        repeat_base += 0.03 if product["expression"] == "Black Label" else 0.0
        repeat_base += 0.06 if product["expression"] == "16" else 0.0
        repeat_prob = float(np.clip(repeat_base + rng.normal(0, 0.05), 0.01, 0.82))
        repeat_flag = int(rng.random() < repeat_prob)

        days_since = None if rng.random() < 0.38 else int(max(5, rng.normal(48 if repeat_flag else 71, 22)))
        units = 1 if rng.random() < 0.91 else int(rng.choice([2, 3], p=[0.75, 0.25]))

        desc_variants = [
            f"{product['brand']} {product['expression']} Scotch {pack_size_ml}ml",
            f"{product['brand']} {product['expression']} {product['whisky_type']}",
            f"{product['brand']} {product['expression']} single malt gift box" if is_gift_boxed else f"{product['brand']} {product['expression']} {pack_size_ml}ml",
        ]
        shelf_variants = [
            f"{product['brand']} {product['expression']} {pack_size_ml}ML",
            f"{product['brand']} {product['expression']} Gift" if is_gift_boxed else f"{product['brand']} {product['expression']}",
            f"{product['brand'].replace('Johnnie Walker','JW')} {product['expression']} {pack_size_ml}",
        ]
        promo_variants = ["", "gift ready bottle special", "price drop while stock lasts", "featured whisky offer", "limited shelf offer"]
        note_variants = [
            "",
            "picked from the feature end after a long look",
            "repeat-looking purchase, no real hesitation",
            "shopper hovered, then came back after another aisle",
            "looked like a gift decision more than a regular buy",
            "premium shelf got traffic, but not much conversion late week",
        ]

        rows.append(
            {
                "brand": product["brand"],
                "expression": product["expression"],
                "whisky_type": product["whisky_type"],
                "age_statement": product["age_statement"],
                "pack_size_ml": pack_size_ml,
                "bottle_price": price,
                "price_band": price_band,
                "is_gift_boxed": is_gift_boxed,
                "peat_profile": product["peat_profile"],
                "tier": product["tier"],
                "store_type": store_type,
                "shelf_zone": shelf_zone,
                "display_type": display_type,
                "promo_flag": promo_flag,
                "city_region": city_region,
                "week": week,
                "purchase_type": purchase_type,
                "occasion": occasion,
                "basket_role": basket_role,
                "repeat_purchase_flag": repeat_flag,
                "days_since_last_purchase": days_since,
                "units_bought": units,
                "estimated_buyer_stage": stage,
                "product_desc_raw": str(rng.choice(desc_variants)),
                "shelf_tag_raw": str(rng.choice(shelf_variants)),
                "promo_text_raw": str(rng.choice(promo_variants)),
                "notes_text": str(rng.choice(note_variants)),
            }
        )

    df = pd.DataFrame(rows)
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)


if __name__ == "__main__":
    main()
