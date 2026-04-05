# Scotch Whisky: Consumer Progression & Premiumization Intelligence

This case study looks at how shoppers move from familiar entry Scotch into more distinctive premium bottles, and where price, packaging, and retail presentation either support that journey or interrupt it.

## Business Question

What signals suggest that a consumer is progressing from accessible Scotch into more distinctive premium whisky, and where do pricing, packaging, and retail presentation influence or interrupt that journey?

## Dataset Overview

The project uses a synthetic but commercially believable retail dataset shaped around purchase moments, shelf context, product cues, and imperfect repeat behaviour.

- `scotch_progression_observations.csv`: purchase and exposure observations across eight Scotch expressions
- `validation_summary.json`: key progression reads from the final build
- `insights.md`: decision-oriented commercial findings

## Methodology

- Built a reproducible synthetic dataset with `random_state=42`
- Preserved missing values, naming inconsistencies, and imperfect flags to keep the dataset believable
- Analysed gateway products, destination products, price friction, gifting, display influence, and stalling points
- Exported visuals for a standalone GitHub Pages walkthrough and a linked III.IV case file

## Key Findings

- Johnnie Walker Black Label acts as the strongest gateway product in the final build.
- Lagavulin 16 behaves most like a destination product: lower frequency, stronger commitment.
- The first clear price friction sits in the `R320-R420` jump.
- Gift packaging widens trial more easily than it builds repeat.
- Standard shelf presence still matters more for loyalty than feature theatre does.

## Validation Snapshot

- Dataset rows: `3,200`
- Strongest gateway product: `Johnnie Walker Black Label`
- Strongest destination product: `Lagavulin 16`
- Biggest friction point: `R320-R420`

## Repo Structure

```text
data/
notebooks/
assets/
docs/
outputs/
src/
README.md
insights.md
requirements.txt
```

## Links

- Live GitHub Pages link: https://km-webdvlpr.github.io/scotch-whisky-consumer-progression-intelligence/
- Portfolio link: https://km-webdvlpr.github.io/III.IV/projects/scotch-whisky-consumer-progression-intelligence/
