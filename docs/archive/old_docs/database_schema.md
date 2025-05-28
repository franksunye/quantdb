# QuantDB Database Schema

This document describes the database schema for the QuantDB project.

## Overview

The QuantDB database schema is designed to store financial data, including:

- Assets (stocks, indices, etc.)
- Price data (historical and real-time)
- Trading signals and plans
- Portfolio information
- Performance metrics

## Entity Relationship Diagram

```
+---------------+       +---------------+       +------------------+
|    assets     |       |    prices     |       | index_constituents|
+---------------+       +---------------+       +------------------+
| asset_id (PK) |<----->| price_id (PK) |       | constituent_id (PK) |
| symbol        |       | asset_id (FK) |       | index_name      |
| name          |       | date          |       | asset_id (FK)   |
| isin          |       | open          |       | inclusion_date  |
| asset_type    |       | high          |       | exclusion_date  |
| exchange      |       | low           |       +------------------+
| currency      |       | close         |
+---------------+       | volume        |       +------------------+
        |               | adjusted_close|       |    indicators    |
        |               +---------------+       +------------------+
        |                                       | indicator_id (PK)|
        |                                       | asset_id (FK)    |
        |                                       | date             |
        |                                       | indicator_type   |
        |                                       | value            |
        |                                       +------------------+
        |
        |               +------------------+    +------------------+
        |               |  trade_signals   |    |   trade_plans    |
        |               +------------------+    +------------------+
        |               | signal_id (PK)   |    | plan_id (PK)     |
        |               | strategy_id (FK) |    | plan_date        |
        +-------------->| asset_id (FK)    |<---| signal_id (FK)   |
        |               | signal_date      |    | asset_id (FK)    |
        |               | signal_type      |    | status           |
        |               | signal_strength  |    | entry_price      |
        |               | price_at_signal  |    | exit_price       |
        |               | notes            |    | pnl              |
        |               +------------------+    +------------------+
        |
        |               +------------------+    +------------------+
        |               | daily_stock_data |    |intraday_stock_data|
        |               +------------------+    +------------------+
        |               | id (PK)          |    | id (PK)          |
        +-------------->| asset_id (FK)    |    | asset_id (FK)    |
                        | trade_date       |    | capture_time     |
                        | open             |    | trade_date       |
                        | high             |    | latest_price     |
                        | low              |    | pct_change       |
                        | close            |    | volume           |
                        | volume           |    | ...              |
                        | ...              |    +------------------+
                        +------------------+
```

## Tables

### assets

Stores information about financial assets (stocks, indices, etc.).

| Column | Type | Description |
|--------|------|-------------|
| asset_id | INTEGER | Primary key |
| symbol | TEXT | Asset symbol (e.g., "AAPL") |
| name | TEXT | Asset name (e.g., "Apple Inc.") |
| isin | TEXT | International Securities Identification Number |
| asset_type | TEXT | Type of asset (e.g., "stock", "index") |
| exchange | TEXT | Exchange where the asset is traded |
| currency | TEXT | Currency of the asset |

### prices

Stores historical price data for assets.

| Column | Type | Description |
|--------|------|-------------|
| price_id | INTEGER | Primary key |
| asset_id | INTEGER | Foreign key to assets table |
| date | DATE | Date of the price data |
| open | REAL | Opening price |
| high | REAL | Highest price |
| low | REAL | Lowest price |
| close | REAL | Closing price |
| volume | REAL | Trading volume |
| adjusted_close | REAL | Adjusted closing price |

### index_constituents

Stores the constituents of indices.

| Column | Type | Description |
|--------|------|-------------|
| constituent_id | INTEGER | Primary key |
| index_name | TEXT | Name of the index |
| asset_id | INTEGER | Foreign key to assets table |
| inclusion_date | DATE | Date when the asset was included in the index |
| exclusion_date | DATE | Date when the asset was excluded from the index (if applicable) |

### indicators

Stores technical indicators for assets.

| Column | Type | Description |
|--------|------|-------------|
| indicator_id | INTEGER | Primary key |
| asset_id | INTEGER | Foreign key to assets table |
| date | DATE | Date of the indicator value |
| indicator_type | TEXT | Type of indicator (e.g., "MA", "RSI") |
| value | REAL | Value of the indicator |

### trade_signals

Stores trading signals generated by strategies.

| Column | Type | Description |
|--------|------|-------------|
| signal_id | INTEGER | Primary key |
| strategy_id | INTEGER | Foreign key to strategies table |
| asset_id | INTEGER | Foreign key to assets table |
| signal_date | DATE | Date of the signal |
| signal_type | TEXT | Type of signal (e.g., "buy", "sell") |
| signal_strength | REAL | Strength of the signal |
| price_at_signal | REAL | Price at the time of the signal |
| suggested_quantity | INTEGER | Suggested quantity to trade |
| optimal_result | TEXT | Optimal result of the signal |
| notes | TEXT | Additional notes |

### trade_plans

Stores trading plans based on signals.

| Column | Type | Description |
|--------|------|-------------|
| plan_id | INTEGER | Primary key |
| plan_date | DATE | Date of the plan |
| signal_id | INTEGER | Foreign key to trade_signals table |
| asset_id | INTEGER | Foreign key to assets table |
| asset_name | TEXT | Name of the asset |
| symbol | TEXT | Symbol of the asset |
| status | TEXT | Status of the plan (e.g., "PENDING", "ACTIVE", "COMPLETED") |
| entry_price | REAL | Entry price |
| entry_date | DATE | Entry date |
| exit_price | REAL | Exit price |
| exit_date | DATE | Exit date |
| pnl | REAL | Profit and loss |
| net | REAL | Net profit |
| notes | TEXT | Additional notes |

### daily_stock_data

Stores daily stock data.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| asset_id | INTEGER | Foreign key to assets table |
| trade_date | DATE | Trading date |
| open | REAL | Opening price |
| high | REAL | Highest price |
| low | REAL | Lowest price |
| close | REAL | Closing price |
| volume | INTEGER | Trading volume |
| turnover | REAL | Turnover |
| amplitude | REAL | Amplitude |
| pct_change | REAL | Percentage change |
| change | REAL | Change |
| turnover_rate | REAL | Turnover rate |

### intraday_stock_data

Stores intraday stock data.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| asset_id | INTEGER | Foreign key to assets table |
| capture_time | DATETIME | Time of data capture |
| trade_date | DATE | Trading date |
| latest_price | REAL | Latest price |
| pct_change | REAL | Percentage change |
| change | REAL | Change |
| volume | INTEGER | Trading volume |
| turnover | REAL | Turnover |
| amplitude | REAL | Amplitude |
| high | REAL | Highest price |
| low | REAL | Lowest price |
| open | REAL | Opening price |
| prev_close | REAL | Previous closing price |
| is_final | BOOLEAN | Whether this is the final data for the day |
