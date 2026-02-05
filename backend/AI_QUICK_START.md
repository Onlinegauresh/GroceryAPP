# AI Intelligence - Quick Start Guide

## What is AI Intelligence?

SmartKirana AI Intelligence (STEP 5) provides **4 AI-powered business intelligence features** using zero external APIs and pure Python logic:

1. **Demand Forecasting** - Predict next 7 days of sales
2. **Reorder Suggestions** - When and how much to order
3. **Low Stock Alerts** - Time-based risk assessment
4. **Anomaly Detection** - Detect inventory losses

## Getting Started

### Step 1: Ensure Server is Running

```bash
cd backend
python main_with_auth.py
# Server will start on http://localhost:8000
```

### Step 2: Get Your JWT Token

```bash
# Login (if not already done)
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "owner@shop.com",
    "password": "your_password"
  }'

# Response includes "access_token"
# Save it as: TOKEN="your_token_here"
```

### Step 3: Call AI Endpoints

All endpoints require:

- Your JWT token (as Bearer)
- Your shop_id (you own it or are ADMIN)

## Feature 1: Demand Forecasting

### What it does

Predicts how many units you'll sell each day for the next 7 days

### When to use

- **Daily:** Plan purchasing for next week
- **Before placing orders:** Know expected demand
- **When:** Every morning or when deciding stock levels

### API Call

```bash
curl -X GET "http://localhost:8000/api/v1/ai/forecast/1" \
  -H "Authorization: Bearer $TOKEN"
```

### Response Format

```json
{
  "shop_id": 1,
  "generated_at": "2024-01-22T10:30:00Z",
  "forecast_start_date": "2024-01-23",
  "total_products_forecasted": 15,
  "products": [
    {
      "product_id": 101,
      "product_name": "Rice 10kg",
      "current_stock": 45,
      "historical_daily_avg": 3.5,
      "total_predicted_7day": 28,
      "forecasts": [
        {
          "date": "2024-01-23",
          "predicted_quantity": 4,
          "confidence": 0.85,
          "method": "linear_regression"
        }
      ]
    }
  ]
}
```

### What the numbers mean

| Field                  | Meaning                                    |
| ---------------------- | ------------------------------------------ |
| `current_stock`        | Units you have right now                   |
| `historical_daily_avg` | Average daily sales (past 7 days)          |
| `total_predicted_7day` | Total units you'll sell in next 7 days     |
| `confidence`           | How reliable is this forecast (0.0 to 1.0) |
| `method`               | Algorithm used (linear_regression)         |

### Example Action

```
Rice forecast: 28 units in 7 days
Current stock: 45 units
Historical daily avg: 3.5 units

Decision: Stock is sufficient, no need to order immediately
Wait for stock to drop to ~21 units (3 days of buffer)
```

## Feature 2: Reorder Suggestions

### What it does

Tells you EXACTLY which products to order and how many

### When to use

- **Multiple times per day:** Check what needs ordering
- **When placing orders:** Get quantities automatically
- **Weekly review:** Plan bulk orders

### API Call

```bash
curl -X GET "http://localhost:8000/api/v1/ai/reorder-suggestions/1" \
  -H "Authorization: Bearer $TOKEN"
```

### Response Format

```json
{
  "shop_id": 1,
  "generated_at": "2024-01-22T10:30:00Z",
  "total_suggestions": 12,
  "urgent_count": 3,
  "suggestions": [
    {
      "product_id": 102,
      "product_name": "Wheat Flour",
      "current_stock": 5,
      "daily_sales_velocity": 2.1,
      "days_stock_left": 2.4,
      "suggested_reorder_qty": 18,
      "urgent": true
    }
  ]
}
```

### What the numbers mean

| Field                   | Meaning                                |
| ----------------------- | -------------------------------------- |
| `current_stock`         | Units you have right now               |
| `daily_sales_velocity`  | Units you sell per day (on average)    |
| `days_stock_left`       | How many days until you run out        |
| `suggested_reorder_qty` | ORDER THIS MANY UNITS                  |
| `urgent`                | true = order TODAY, false = order soon |

### Example Action

```
Wheat Flour:
  Current stock: 5 units
  Daily velocity: 2.1 units/day
  Days left: 2.4 days
  Suggested order: 18 units
  Urgent: YES ✓

ACTION: Order 18 units of Wheat Flour TODAY
(Stock will finish in 2 days if you don't order)
```

## Feature 3: Low Stock Risk Assessment

### What it does

Categorizes all products by risk level (critical → low)

### When to use

- **Every few hours:** Check what's at risk
- **During peak hours:** Know what might run out
- **Before closing:** Plan next day's stock

### API Call

```bash
curl -X GET "http://localhost:8000/api/v1/ai/low-stock-risk/1" \
  -H "Authorization: Bearer $TOKEN"
```

### Response Format

```json
{
  "shop_id": 1,
  "generated_at": "2024-01-22T10:30:00Z",
  "critical_count": 1,
  "high_risk_count": 2,
  "medium_risk_count": 4,
  "risks": [
    {
      "product_id": 102,
      "product_name": "Wheat Flour",
      "current_stock": 5,
      "min_stock_level": 10,
      "daily_velocity": 2.1,
      "days_until_minimum": 0.8,
      "risk_level": "CRITICAL",
      "action_required": true
    }
  ]
}
```

### Risk Levels Explained

| Risk Level  | Days Until Minimum | Action                                  |
| ----------- | ------------------ | --------------------------------------- |
| 🔴 CRITICAL | < 1 day            | ORDER NOW - Stock will finish today     |
| 🟠 HIGH     | 1-3 days           | ORDER URGENT - Stock finishing soon     |
| 🟡 MEDIUM   | 3-7 days           | PLAN ORDER - Stock may finish in a week |
| 🟢 LOW      | > 7 days           | NO ACTION - Sufficient stock            |

### Example Action

```
Summary:
  Critical items: 1
  High risk items: 2

Wheat Flour: CRITICAL (0.8 days)
  → Call supplier NOW

Cooking Oil: HIGH (2.1 days)
  → Create purchase order today

Sugar: MEDIUM (5.3 days)
  → Schedule order for this week
```

## Feature 4: Anomaly Detection

### What it does

Detects unusual inventory changes (theft, damage, errors)

### When to use

- **Weekly:** Audit inventory accuracy
- **When stock unexpectedly drops:** Investigate cause
- **Monthly reconciliation:** Find discrepancies

### API Call

```bash
curl -X GET "http://localhost:8000/api/v1/ai/anomalies/1?days_back=7" \
  -H "Authorization: Bearer $TOKEN"
```

Query Parameters:

- `days_back` - How many days to analyze (default: 7, max: 30)

### Response Format

```json
{
  "shop_id": 1,
  "generated_at": "2024-01-22T10:30:00Z",
  "period": "2024-01-15 to 2024-01-22",
  "total_anomalies": 2,
  "critical_anomalies": 0,
  "total_loss_detected": "5.50",
  "anomalies": [
    {
      "date": "2024-01-20",
      "product_id": 105,
      "product_name": "Spices Mix",
      "expected_stock_change": 5,
      "actual_stock_change": 8,
      "deviation": 3,
      "deviation_pct": 60.0,
      "severity": "HIGH",
      "possible_causes": ["Bulk order", "Promotional sales"]
    }
  ]
}
```

### What the numbers mean

| Field                   | Meaning                                    |
| ----------------------- | ------------------------------------------ |
| `expected_stock_change` | How much should have sold                  |
| `actual_stock_change`   | How much actually sold                     |
| `deviation`             | Difference (loss/gain)                     |
| `severity`              | HIGH/MEDIUM/LOW based on %, higher = worse |
| `possible_causes`       | Why this might have happened               |

### Severity Levels

| Severity    | Meaning           | Loss % |
| ----------- | ----------------- | ------ |
| 🔴 CRITICAL | Potential theft   | > 50%  |
| 🟠 HIGH     | Significant loss  | 30-50% |
| 🟡 MEDIUM   | Minor discrepancy | 10-30% |
| 🟢 LOW      | Normal variance   | < 10%  |

### Example Action

```
Date: 2024-01-20
Spices Mix:
  Expected to sell: 5 units
  Actually sold: 8 units
  Deviation: +3 units (60% more)
  Severity: HIGH

Possible causes:
  - Bulk order (customer bought extra)
  - Promotional sale (price was reduced)

ACTION: Check sales records for that day
OR investigate if 3 units are actually missing
```

## Dashboard View (Manual Integration)

Combine all 4 features into a dashboard:

```
┌─────────────────────────────────────────────────────────┐
│             SMARTKIRANA - AI INTELLIGENCE               │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  🔴 CRITICAL ITEMS (1)                                  │
│     Wheat Flour  -  0.8 days until stockout   ORDER NOW │
│                                                           │
│  🟠 HIGH RISK (2)                                       │
│     Cooking Oil  -  2.1 days                  ORDER SOON │
│     Spices Mix   -  2.8 days                  ORDER SOON │
│                                                           │
│  🟡 MEDIUM RISK (4)                                     │
│     Rice 10kg    -  4.5 days                  PLAN ORDER │
│     Lentils      -  5.2 days                  PLAN ORDER │
│                                                           │
│  📊 7-DAY FORECAST TOTAL DEMAND: 245 units               │
│     → Current total stock: 380 units                     │
│     → Recommendation: Stock sufficient for week          │
│                                                           │
│  ⚠️  ANOMALIES DETECTED: 2 discrepancies (7 days)       │
│     HIGH: Spices Mix (60% deviation)   → Investigate    │
│     MEDIUM: Sugar (25% deviation)      → Review sales   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Integration Examples

### Example 1: Morning Checklist

```bash
# 1. Check forecast for the day
curl -X GET "http://localhost:8000/api/v1/ai/forecast/1" \
  -H "Authorization: Bearer $TOKEN" | jq '.products[] | select(.product_name=="Top Products")'

# 2. Check urgent reorders
curl -X GET "http://localhost:8000/api/v1/ai/reorder-suggestions/1" \
  -H "Authorization: Bearer $TOKEN" | jq '.suggestions[] | select(.urgent==true)'

# 3. Check critical stock levels
curl -X GET "http://localhost:8000/api/v1/ai/low-stock-risk/1" \
  -H "Authorization: Bearer $TOKEN" | jq '.risks[] | select(.risk_level=="CRITICAL")'
```

### Example 2: Weekly Audit

```bash
# Review anomalies over past 7 days
curl -X GET "http://localhost:8000/api/v1/ai/anomalies/1?days_back=7" \
  -H "Authorization: Bearer $TOKEN"

# High anomalies indicate:
# - Inventory accuracy issues
# - Shrinkage/theft
# - Record-keeping problems
```

### Example 3: Purchase Order Generation

```python
# Python integration example
import requests

TOKEN = "your_jwt_token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Get reorder suggestions
response = requests.get(
    "http://localhost:8000/api/v1/ai/reorder-suggestions/1",
    headers=HEADERS
)

suggestions = response.json()

# Create purchase orders for urgent items
for suggestion in suggestions['suggestions']:
    if suggestion['urgent']:
        print(f"PO: {suggestion['product_name']} - {suggestion['suggested_reorder_qty']} units")
        # Call your purchase_order_system
        # create_purchase_order(suggestion)
```

## Common Scenarios

### Scenario 1: Running Low on Popular Item

```
Forecast shows: 28 units needed in 7 days
Current stock: 5 units
Reorder suggests: 18 units URGENT

→ Stock will finish in 2.4 days
→ Order 18 units TODAY to have buffer
```

### Scenario 2: Slow-Moving Product

```
Forecast: 2 units in 7 days
Current stock: 15 units
Reorder suggests: 0 units

→ Stock will last 50+ days
→ No action needed, stock sufficient
```

### Scenario 3: Unusual Spike

```
Anomaly detected:
  Expected 5 units sold, 12 actually sold
  Deviation: +7 units (140%)

Possible causes:
  - Bulk order
  - Promotional sale
  - Wedding/event

→ Check sales records
→ If real demand spike, increase forecast multiplier
```

### Scenario 4: Inventory Discrepancy

```
Anomaly detected:
  Expected 5 units sold, 2 units sold
  Missing: 3 units
  Severity: HIGH

Possible causes:
  - Theft
  - Damage/expiry
  - Manual removal

→ Physical count the item
→ Document finding
→ Report to management
```

## Tips & Best Practices

### ✅ Do's

- ✅ Check forecasts daily
- ✅ Act on URGENT reorders immediately
- ✅ Review anomalies weekly
- ✅ Use confidence scores to validate forecasts
- ✅ Combine multiple signals before deciding
- ✅ Document any manual adjustments

### ❌ Don'ts

- ❌ Ignore CRITICAL risk alerts
- ❌ Over-order based on forecast alone
- ❌ Treat anomalies as definitive proof
- ❌ Rely solely on AI (human judgment matters)
- ❌ Use forecast for more than 7 days out
- ❌ Forget to check lead times

## Troubleshooting

### Issue: No forecast for a product

**Reason:** Product has no sales history
**Solution:** Wait for first few sales, then forecast will activate

### Issue: Reorder quantity seems too high

**Reason:** Using 1.5× multiplier for safety buffer
**Solution:** Review your lead time and ordering frequency
OR manually adjust down if you prefer

### Issue: Anomaly alerts too frequent

**Reason:** High volatility in sales (50%+ variation)
**Solution:** Check if promotions are causing spikes
OR wait for more stable data (14+ days)

### Issue: Low stock alert not triggered

**Reason:** Product has slow velocity
**Solution:** Check if min_stock_level is too high
OR product is genuinely slow-moving (no action needed)

## Performance Notes

- ✅ All requests complete in < 1 second
- ✅ No database locking or slowdowns
- ✅ Safe to call multiple times per second
- ✅ Designed for real-time decisions

## Next Steps

1. **Monitor daily** - Set reminders to check critical items
2. **Act on urgent** - Don't ignore CRITICAL status
3. **Review weekly** - Look for patterns in anomalies
4. **Iterate** - Adjust min stock levels based on experience
5. **Automate** - Consider auto-generating purchase orders

## Support

For detailed information, see: **AI_INTELLIGENCE_DOCUMENTATION.md**

## Summary

SmartKirana AI gives you:

- 📊 **7-day demand predictions** - Plan ahead
- 📦 **Smart reorder suggestions** - Never stockout
- 🎯 **Time-based alerts** - Act before crisis
- 🔍 **Anomaly detection** - Spot problems

All for **free, with zero external API costs.**

**Start using AI Intelligence today!**
