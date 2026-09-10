# Airbnb NYC Dataset — Cleaned & Ready to Import

## What's in this file
`airbnb_nyc_cleaned.csv` / `.xlsx` — **256 real NYC Airbnb listings**, pulled from the public "Inside Airbnb" 2019 dataset, cleaned and ready to drop straight into Power BI or Tableau.

**Honest note on size:** the full source file has ~49,000 listings (7MB), which is too large for me to pull through in one pass here. This is a real, working subset — plenty to build and demo every chart in the project plan. See below if you want the full dataset.

## Columns
| Column | What it is |
|---|---|
| `id`, `name`, `host_id`, `host_name` | Listing/host identifiers |
| `neighbourhood_group`, `neighbourhood` | Borough and neighborhood |
| `latitude`, `longitude` | For map visuals |
| `room_type` | Entire home/apt, Private room, Shared room |
| `price` | Nightly price (USD) |
| `price_bucket` | *(new)* Budget / Mid / Premium / Luxury — for easy filtering |
| `minimum_nights`, `number_of_reviews`, `reviews_per_month`, `last_review` | Booking activity |
| `value_score` | *(new)* `number_of_reviews ÷ price` — a simple "bookings per dollar" metric; higher = better perceived value |
| `calculated_host_listings_count` | How many listings that host runs |
| `is_power_host` | *(new)* Yes/No — hosts with 2+ listings and steady review activity (proxy for "superhost"-style quality, since this file has no star ratings) |
| `availability_365` | Days available in the next year |
| `occupancy_pct` | *(new)* `(365 − availability_365) / 365` — rough occupancy estimate |

## Cleaning already done
- Missing `reviews_per_month` → filled with 0 (no reviews yet)
- Missing `last_review` → labeled "No reviews yet"
- Missing host/listing names → labeled "Unknown"/"Unnamed"
- Removed listings with `price = 0` (data errors)
- No nulls remain anywhere in the file

## Getting the full ~49,000-row dataset (optional)
1. Go to **insideairbnb.com/get-the-data.html**
2. Under New York City, download `listings.csv` (or any other city — the columns are the same)
3. Run this Python snippet to apply the exact same cleaning/calculated columns used here:

```python
import pandas as pd, numpy as np

df = pd.read_csv('listings.csv')  # your downloaded file

df['reviews_per_month'] = df['reviews_per_month'].fillna(0)
df['last_review'] = df['last_review'].fillna('No reviews yet')
df = df[df['price'] > 0].copy()

df['is_power_host'] = np.where(
    (df['calculated_host_listings_count'] >= 2) & (df['reviews_per_month'] >= 1),
    'Yes', 'No')
df['value_score'] = (df['number_of_reviews'] / df['price']).round(3)
df['occupancy_pct'] = ((365 - df['availability_365']) / 365 * 100).round(1)
df['price_bucket'] = pd.cut(df['price'], [0,75,150,300,float('inf')],
    labels=['Budget (<$75)','Mid ($75-149)','Premium ($150-299)','Luxury ($300+)'])

df.to_csv('airbnb_cleaned_full.csv', index=False)
```

## Next step
Open `airbnb_nyc_cleaned.xlsx` (or the `.csv`) directly in Power BI Desktop or Tableau — no further prep needed — and start building the pages from the project plan (Overview, Pricing, Host Quality, Seasonality).
