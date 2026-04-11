from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import nbformat as nbf
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "scotch_progression_observations.csv"
OUTPUTS_DIR = ROOT / "outputs"
INSIGHTS_PATH = ROOT / "insights.md"
README_PATH = ROOT / "README.md"
NOTEBOOK_PATH = ROOT / "notebooks" / "scotch_progression_intelligence.ipynb"


def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


def build_product_progression_summary(df: pd.DataFrame) -> pd.DataFrame:
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
            gift_share=("purchase_type", lambda s: (s == "gift").mean()),
            display_feature_share=("shelf_zone", lambda s: (s == "feature_display").mean()),
            tier=("tier", "first"),
        )
    )

    product_view["gateway_score"] = (
        product_view["observations"]
        * (product_view["entry_familiar_share"] * 0.62 + product_view["preference_share"] * 0.38)
        * product_view["self_share"]
        * (product_view["avg_price"] / 420).clip(0.85, 1.35)
        * (1 - (product_view["repeat_rate"] - 0.28).abs())
    ).round(3)

    product_view["destination_score"] = (
        product_view["repeat_rate"]
        * product_view["preference_share"]
        * product_view["avg_price"].map(np.log1p)
    ).round(3)

    product_view = product_view.sort_values(["gateway_score", "destination_score"], ascending=False)
    product_view.to_csv(OUTPUTS_DIR / "product_progression_summary.csv", index=False)
    return product_view


def build_price_friction_summary(df: pd.DataFrame) -> pd.DataFrame:
    friction = (
        df.assign(
            price_step=pd.cut(
                df["bottle_price"],
                bins=[0, 320, 420, 520, 700, 950, 1400, 1800],
                include_lowest=True,
                labels=["Under R320", "R320-R420", "R420-R520", "R520-R700", "R700-R950", "R950-R1400", "R1400+"],
            )
        )
        .groupby("price_step", as_index=False, observed=False)
        .agg(
            observations=("brand", "size"),
            repeat_rate=("repeat_purchase_flag", "mean"),
            exploratory_share=("estimated_buyer_stage", lambda s: s.isin(["exploratory", "preference_led"]).mean()),
        )
    )
    friction["drop_vs_prev"] = friction["repeat_rate"].diff()
    friction["tension_gap"] = (friction["exploratory_share"] - friction["repeat_rate"]).round(3)
    friction.to_csv(OUTPUTS_DIR / "price_friction_summary.csv", index=False)
    return friction


def build_gift_packaging_summary(df: pd.DataFrame) -> pd.DataFrame:
    gift = (
        df.groupby(["is_gift_boxed", "purchase_type"], as_index=False)
        .agg(
            observations=("brand", "size"),
            repeat_rate=("repeat_purchase_flag", "mean"),
            preference_led_share=("estimated_buyer_stage", lambda s: (s == "preference_led").mean()),
        )
        .sort_values(["is_gift_boxed", "purchase_type"])
    )
    gift["gift_boxed_label"] = gift["is_gift_boxed"].map({0: "Standard pack", 1: "Gift boxed"})
    gift.to_csv(OUTPUTS_DIR / "gift_packaging_summary.csv", index=False)
    return gift


def build_display_effect_summary(df: pd.DataFrame) -> pd.DataFrame:
    display = (
        df.groupby(["display_type", "shelf_zone"], as_index=False)
        .agg(
            observations=("brand", "size"),
            repeat_rate=("repeat_purchase_flag", "mean"),
            exploratory_share=("estimated_buyer_stage", lambda s: s.isin(["exploratory", "preference_led"]).mean()),
            self_purchase_share=("purchase_type", lambda s: (s == "self").mean()),
        )
        .sort_values(["display_type", "shelf_zone"])
    )
    display.to_csv(OUTPUTS_DIR / "display_effect_summary.csv", index=False)
    return display


def build_stage_stall_summary(df: pd.DataFrame) -> pd.DataFrame:
    stall = (
        df.groupby(["estimated_buyer_stage", "price_band"], as_index=False)
        .agg(
            observations=("brand", "size"),
            repeat_rate=("repeat_purchase_flag", "mean"),
            gift_share=("purchase_type", lambda s: (s == "gift").mean()),
        )
        .sort_values(["estimated_buyer_stage", "price_band"])
    )
    stall.to_csv(OUTPUTS_DIR / "stage_stall_summary.csv", index=False)
    return stall


def build_validation_summary(
    df: pd.DataFrame,
    product_summary: pd.DataFrame,
    friction: pd.DataFrame,
) -> dict[str, object]:
    gateway_product = (
        product_summary.loc[product_summary["tier"].isin(["core", "premium"])]
        .sort_values("gateway_score", ascending=False)
        .iloc[0]["product_key"]
    )
    destination_product = product_summary.sort_values("destination_score", ascending=False).iloc[0]["product_key"]
    eligible = friction.loc[(friction["price_step"] != "Under R320") & (friction["observations"] >= 150)].copy()
    first_tight_step = eligible.loc[eligible["tension_gap"] > 0.05].head(1)
    biggest_friction_step = (
        first_tight_step.iloc[0]["price_step"]
        if not first_tight_step.empty
        else friction.sort_values("drop_vs_prev").iloc[0]["price_step"]
    )

    summary = {
        "dataset_rows": int(len(df)),
        "gateway_product": str(gateway_product),
        "destination_product": str(destination_product),
        "biggest_friction_step": str(biggest_friction_step),
        "gateway_rule": "Gateway score combines volume, early-stage buyer share, self-purchase share, price fit, and moderate repeat behaviour.",
        "destination_rule": "Destination score combines repeat rate, later-stage buyer share, and price intensity.",
        "friction_rule": "The friction step is the first price band where exploratory interest clearly runs ahead of repeat, with low-volume bands excluded.",
        "insights_present": INSIGHTS_PATH.exists(),
        "notebook_present": NOTEBOOK_PATH.exists(),
    }
    (OUTPUTS_DIR / "validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def write_insights(summary: dict[str, object]) -> None:
    text = f"""INSIGHT
Gateway movement starts with familiar labels, not dramatic leaps.
FINDING
{summary['gateway_product']} carries the highest gateway score once early-stage buyer mix, self-purchase behaviour, and scale are read together.
SO WHAT
In this model, progression starts where shoppers still feel they recognise the bottle. The move upward is more of a guided step than a dramatic leap.
RECOMMENDATION
Use gateway bottles to frame the shelf ladder. Keep them close to more premium cues rather than isolating them in the value block.

INSIGHT
Destination bottles are defined by commitment, not just price.
FINDING
{summary['destination_product']} ranks highest on the destination score, which leans more heavily on repeat, later-stage buyer mix, and price intensity.
SO WHAT
The top end is not where most shoppers start, but it is where a smaller group becomes much clearer about what they like.
RECOMMENDATION
Merchandise destination bottles with flavour language and confidence cues, not only prestige cues.

INSIGHT
The first price stretch still does most of the damage.
FINDING
The first clear tension in the model sits in the {summary['biggest_friction_step']} band.
SO WHAT
Shoppers often browse upward before they are willing to stay there. Interest is not the same thing as comfort.
RECOMMENDATION
Make the first premium stretch easier to understand with comparison, flavour cues, or a clearer why-this-costs-more story.

INSIGHT
Gift packaging helps trial more than it helps habit.
FINDING
Gift-boxed bottles widen gift-led and occasion-led purchase, but they do not become the strongest repeat performers in the model.
SO WHAT
Packaging can open the door without creating a relationship. That is useful, but it should not be mistaken for loyalty.
RECOMMENDATION
Use gift packaging as a seasonal recruitment tool, then hand off repeat-building to the standard shelf and clearer flavour cues.

INSIGHT
Standard shelf space is still doing the quieter loyalty work.
FINDING
Feature displays and promo stacks help discovery, but steadier repeat sits more often in standard shelf conditions.
SO WHAT
Discovery and habit are not built in the same place.
RECOMMENDATION
Separate recruitment space from habit space in retail planning. Let displays seed trial, but protect the core shelf for follow-up purchase.
"""
    INSIGHTS_PATH.write_text(text, encoding="utf-8")


def write_readme(summary: dict[str, object]) -> None:
    text = f"""# Scotch Whisky: Consumer Progression & Premiumization Intelligence

This case study uses a synthetic Scotch retail dataset to look at how shoppers move from accessible bottles into more distinctive premium expressions, and where price, packaging, and shelf context interrupt that climb.

## Business Question

What signals suggest that a shopper is progressing from accessible Scotch into more distinctive premium whisky, and where do pricing, packaging, and retail presentation influence or interrupt that journey?

## Dataset Overview

The project uses a synthetic but commercially believable retail dataset shaped around purchase moments, shelf context, product cues, and imperfect repeat behaviour.

- `scotch_progression_observations.csv`: purchase and exposure observations across eight Scotch expressions
- `product_progression_summary.csv`: product-role summary including gateway and destination scoring
- `price_friction_summary.csv`: repeat-rate movement across price bands
- `gift_packaging_summary.csv`: gift boxing versus repeat and purchase context
- `display_effect_summary.csv`: display and shelf effects on discovery and repeat
- `stage_stall_summary.csv`: buyer-stage and price-band view of progression friction
- `validation_summary.json`: headline summary from the final build

## Methodology

- Built a reproducible synthetic dataset with `random_state=42`
- Preserved missing values, naming inconsistencies, and imperfect text fields so the retail picture does not feel artificially clean
- Scored gateway products using early-stage buyer mix, self-purchase share, scale, and moderate repeat behaviour
- Scored destination products using repeat, later-stage buyer mix, and price intensity
- Flagged the main friction step as the first price band where exploratory interest clearly runs ahead of repeat

## Interpretation notes

- This is a synthetic case study designed to test progression logic, not a claim about live Scotch retail data
- The gateway and destination labels come from weighted scores, so they should be read as structured heuristics rather than fixed truths
- The friction read is a simple repeat-rate heuristic by price band, not a causal elasticity model
- The supporting output tables are there to make those heuristics easier to inspect

## Key Findings

- Strongest gateway product: `{summary['gateway_product']}`
- Strongest destination product: `{summary['destination_product']}`
- Biggest friction point: `{summary['biggest_friction_step']}`
- Dataset rows: `{summary['dataset_rows']:,}`

## Links

- Live GitHub Pages link: https://km-webdvlpr.github.io/scotch-whisky-consumer-progression-intelligence/
- Portfolio link: https://km-webdvlpr.github.io/III.IV/projects/scotch-whisky-consumer-progression-intelligence/
"""
    README_PATH.write_text(text, encoding="utf-8")


def write_notebook() -> None:
    nb = nbf.v4.new_notebook()
    cells = [
        nbf.v4.new_markdown_cell(
            "# Scotch Whisky: Consumer Progression & Premiumization Intelligence\n"
            "This notebook is a light analytical companion to the exported outputs."
        ),
        nbf.v4.new_markdown_cell(
            "## Setup\n"
            "**Business question:** What signals suggest that a shopper is progressing into more premium Scotch, and where does that movement tighten?"
        ),
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "import pandas as pd\n"
            "ROOT = Path('..').resolve()\n"
            "data = pd.read_csv(ROOT / 'data' / 'scotch_progression_observations.csv')\n"
            "product = pd.read_csv(ROOT / 'outputs' / 'product_progression_summary.csv')\n"
            "friction = pd.read_csv(ROOT / 'outputs' / 'price_friction_summary.csv')\n"
            "gift = pd.read_csv(ROOT / 'outputs' / 'gift_packaging_summary.csv')\n"
            "display = pd.read_csv(ROOT / 'outputs' / 'display_effect_summary.csv')\n"
            "data.head()"
        ),
        nbf.v4.new_markdown_cell("## Product role\n**Business question:** Which bottles look like gateways and which ones look more like destinations?"),
        nbf.v4.new_code_cell("product[['product_key','gateway_score','destination_score','observations','repeat_rate']].head(10)"),
        nbf.v4.new_markdown_cell("## Price friction\n**Business question:** Where does repeat soften most clearly as price steps up?"),
        nbf.v4.new_code_cell("friction"),
        nbf.v4.new_markdown_cell("## Gift packaging\n**Business question:** Does gift packaging widen reach more than it builds repeat?"),
        nbf.v4.new_code_cell("gift"),
        nbf.v4.new_markdown_cell("## Display conditions\n**Business question:** Which display conditions seem to recruit trial, and which ones support repeat?"),
        nbf.v4.new_code_cell("display.head(12)"),
    ]
    nb["cells"] = cells
    NOTEBOOK_PATH.write_text(nbf.writes(nb), encoding="utf-8")


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()
    product_summary = build_product_progression_summary(df)
    friction = build_price_friction_summary(df)
    build_gift_packaging_summary(df)
    build_display_effect_summary(df)
    build_stage_stall_summary(df)
    summary = build_validation_summary(df, product_summary, friction)
    write_insights(summary)
    write_readme(summary)
    write_notebook()


if __name__ == "__main__":
    main()
