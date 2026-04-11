# Scotch Whisky: Consumer Progression & Premiumization Intelligence

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

- Strongest gateway product: `Johnnie Walker Black Label`
- Strongest destination product: `Lagavulin 16`
- Biggest friction point: `R320-R420`
- Dataset rows: `3,200`

## Links

- Live GitHub Pages link: https://km-webdvlpr.github.io/scotch-whisky-consumer-progression-intelligence/
- Portfolio link: https://km-webdvlpr.github.io/III.IV/projects/scotch-whisky-consumer-progression-intelligence/
