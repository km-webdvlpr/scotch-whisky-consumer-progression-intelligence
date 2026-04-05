from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "scotch_progression_observations.csv"
INSIGHTS_PATH = ROOT / "insights.md"
NOTEBOOK_PATH = ROOT / "notebooks" / "scotch_progression_intelligence.ipynb"
OUTPUTS_PATH = ROOT / "outputs" / "validation_summary.json"


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    product_view = (
        df.assign(product_key=df["brand"] + " " + df["expression"].astype(str))
        .groupby("product_key", as_index=False)
        .agg(
            observations=("brand", "size"),
            repeat_rate=("repeat_purchase_flag", "mean"),
            entry_familiar_share=("estimated_buyer_stage", lambda s: s.isin(["entry", "familiar"]).mean()),
            preference_share=("estimated_buyer_stage", lambda s: s.isin(["exploratory", "preference_led"]).mean()),
            avg_price=("bottle_price", "mean"),
            self_share=("purchase_type", lambda s: (s == "self").mean()),
            tier=("tier", "first"),
        )
    )

    product_view["gateway_score"] = (
        product_view["observations"]
        * (product_view["entry_familiar_share"] * 0.62 + product_view["preference_share"] * 0.38)
        * product_view["self_share"]
        * (product_view["avg_price"] / 420).clip(0.85, 1.35)
        * (1 - (product_view["repeat_rate"] - 0.28).abs())
    )
    gateway_product = (
        product_view.loc[product_view["tier"].isin(["core", "premium"])]
        .sort_values("gateway_score", ascending=False)
        .iloc[0]["product_key"]
    )
    destination_product = (
        product_view.assign(destination_score=product_view["repeat_rate"] * product_view["preference_share"] * product_view["avg_price"].map(np.log1p))
        .sort_values("destination_score", ascending=False)
        .iloc[0]["product_key"]
    )

    friction_table = (
        df.assign(
            price_step=pd.cut(
                df["bottle_price"],
                bins=[0, 320, 420, 520, 700, 950, 1400, 1800],
                include_lowest=True,
            ).astype(str)
        )
        .groupby("price_step", as_index=False)
        .agg(repeat_rate=("repeat_purchase_flag", "mean"))
    )
    friction_table["drop_vs_prev"] = friction_table["repeat_rate"].diff()
    friction_map = {
        "(-0.001, 320.0]": "Under R320",
        "(320.0, 420.0]": "R320-R420",
        "(420.0, 520.0]": "R420-R520",
        "(520.0, 700.0]": "R520-R700",
        "(700.0, 950.0]": "R700-R950",
        "(950.0, 1400.0]": "R950-R1400",
        "(1400.0, 1800.0]": "R1400+",
    }
    biggest_friction_step = friction_map[friction_table.sort_values("drop_vs_prev").iloc[0]["price_step"]]

    summary = {
        "dataset_rows": int(len(df)),
        "gateway_product": gateway_product,
        "destination_product": destination_product,
        "biggest_friction_step": biggest_friction_step,
        "key_signal": "Gateway bottles are not just cheaper; they are the ones that still look safe enough for self-purchase while nudging shoppers into a clearer style cue or price step.",
        "insights_present": INSIGHTS_PATH.exists(),
        "notebook_present": NOTEBOOK_PATH.exists(),
    }
    OUTPUTS_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
