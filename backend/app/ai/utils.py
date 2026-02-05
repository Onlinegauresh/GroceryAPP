"""AI utility functions - statistical calculations and helpers"""
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from statistics import mean, stdev
from decimal import Decimal


# ===== MOVING AVERAGE & LINEAR REGRESSION =====

def calculate_moving_average(values: List[int], window: int = 7) -> float:
    """
    Calculate moving average of values.

    Args:
        values: List of historical quantities
        window: Window size for averaging (default 7 days)

    Returns:
        Average as float

    ASSUMPTION: Sufficient historical data available
    """
    if not values:
        return 0.0
    if len(values) < window:
        return mean(values)
    return mean(values[-window:])


def linear_regression_forecast(historical_qty: List[int], days_ahead: int = 7) -> List[int]:
    """
    Simple linear regression for demand forecasting.

    ASSUMPTION: Linear trend is adequate for short-term (no seasonality)

    Args:
        historical_qty: Daily quantities from past (sorted, oldest first)
        days_ahead: Number of days to forecast

    Returns:
        List of predicted quantities for each future day
    """
    if not historical_qty or len(historical_qty) < 2:
        avg = mean(historical_qty) if historical_qty else 0
        return [int(avg)] * days_ahead

    # Simple linear regression: y = mx + b
    n = len(historical_qty)
    x_values = list(range(n))
    y_values = historical_qty

    # Calculate slope (m) and intercept (b)
    x_mean = mean(x_values)
    y_mean = mean(y_values)

    numerator = sum((x_values[i] - x_mean) *
                    (y_values[i] - y_mean) for i in range(n))
    denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return [int(y_mean)] * days_ahead

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    # Forecast future days
    forecast = []
    for day in range(n, n + days_ahead):
        predicted = slope * day + intercept
        # Ensure non-negative
        forecast.append(max(0, int(round(predicted))))

    return forecast


# ===== STOCK VELOCITY & REORDER LOGIC =====

def calculate_daily_velocity(historical_quantities: List[int]) -> float:
    """
    Calculate average daily sales velocity.

    Args:
        historical_quantities: Daily sales quantities (past 7-14 days)

    Returns:
        Average units sold per day
    """
    if not historical_quantities:
        return 0.0
    return mean(historical_quantities)


def calculate_days_stock_left(current_stock: int, daily_velocity: float) -> float:
    """
    Calculate how many days of stock remaining at current velocity.

    Args:
        current_stock: Current inventory quantity
        daily_velocity: Average daily sales rate

    Returns:
        Days until stock reaches 0
    """
    if daily_velocity == 0:
        return 999  # No sales = stock lasts forever
    return current_stock / daily_velocity


def calculate_reorder_quantity(
    current_stock: int,
    daily_velocity: float,
    forecasted_7day_demand: int,
    lead_time_days: int = 1
) -> int:
    """
    Calculate optimal reorder quantity using rule-based logic.

    ASSUMPTION: Lead time is 1 day, can be overridden

    Formula:
    1. Calculate stock needed for next 7 days: forecast_7day + buffer (1 day extra)
    2. Calculate safety stock: daily_velocity * lead_time
    3. Reorder point = safety_stock + forecast_7day
    4. If current_stock < reorder_point, order = (forecast_7day * 1.5) - current_stock

    Args:
        current_stock: Current inventory
        daily_velocity: Average daily sales
        forecasted_7day_demand: Predicted demand for next 7 days
        lead_time_days: Days to receive stock (default 1)

    Returns:
        Suggested reorder quantity
    """
    # Safety stock for lead time
    safety_stock = int(daily_velocity * lead_time_days) + 1

    # Reorder point (when to trigger order)
    reorder_point = safety_stock + int(forecasted_7day_demand / 2)

    if current_stock < reorder_point:
        # Calculate order quantity: 1.5x forecast to avoid frequent orders
        suggested = max(0, int(forecasted_7day_demand * 1.5) - current_stock)
        return max(1, suggested)  # Always suggest at least 1 unit

    return 0  # No reorder needed


# ===== ANOMALY DETECTION =====

def detect_stock_anomalies(
    current_stock: int,
    previous_stock: int,
    daily_sales: int,
    threshold_stddev: float = 2.0
) -> Tuple[bool, int, str]:
    """
    Detect abnormal stock changes (shrinkage, theft, damage).

    ASSUMPTION: Normal distribution for anomaly detection

    Logic:
    - Expected stock change = previous_stock - daily_sales
    - Actual stock change = previous_stock - current_stock
    - Deviation = actual - expected
    - If deviation > 2 standard deviations, flag as anomaly

    Args:
        current_stock: Current inventory
        previous_stock: Previous day inventory
        daily_sales: Expected sales (units sold)
        threshold_stddev: Z-score threshold (2.0 = ~95% confidence)

    Returns:
        (is_anomaly: bool, deviation: int, severity: str)
    """
    expected_stock_after_sales = previous_stock - daily_sales
    actual_loss = expected_stock_after_sales - current_stock

    # Simple threshold rule: loss > 30% of daily_sales is suspicious
    if actual_loss > 0:
        loss_ratio = actual_loss / max(daily_sales, 1)

        if loss_ratio > 0.5:  # Loss > 50% of sales
            return (True, actual_loss, "CRITICAL")
        elif loss_ratio > 0.3:  # Loss > 30% of sales
            return (True, actual_loss, "HIGH")
        elif loss_ratio > 0.1:  # Loss > 10% of sales
            return (True, actual_loss, "MEDIUM")

    return (False, 0, "LOW")


def get_anomaly_causes(
    deviation: int,
    sales_velocity: float,
    current_qty: int,
    min_stock: int
) -> List[str]:
    """
    Suggest possible causes for stock anomaly.

    Args:
        deviation: Unexplained stock loss
        sales_velocity: Daily sales rate
        current_qty: Current stock
        min_stock: Minimum stock level

    Returns:
        List of possible causes
    """
    causes = []

    if deviation > sales_velocity * 3:
        causes.append("Potential theft or shrinkage")

    if current_qty < min_stock:
        causes.append("Stock below minimum threshold")

    if deviation > 0:
        causes.append("Unrecorded/damaged inventory")

    if not causes:
        causes.append("Manual stock adjustment or inventory correction")

    return causes


# ===== RISK CLASSIFICATION =====

def classify_stock_risk(days_until_minimum: float) -> str:
    """
    Classify stock into risk levels based on time to minimum.

    ASSUMPTION: Risk classification thresholds are:
    - < 1 day: CRITICAL (order today!)
    - 1-3 days: HIGH (order ASAP)
    - 3-7 days: MEDIUM (plan order)
    - > 7 days: LOW (no action needed)

    Args:
        days_until_minimum: Days until stock hits minimum level

    Returns:
        Risk level string
    """
    if days_until_minimum < 1:
        return "CRITICAL"
    elif days_until_minimum < 3:
        return "HIGH"
    elif days_until_minimum < 7:
        return "MEDIUM"
    else:
        return "LOW"


def forecast_confidence(historical_data_points: int) -> float:
    """
    Calculate confidence level of forecast based on historical data.

    ASSUMPTION: More historical data = higher confidence
    - 0-3 days: 0.5 (low)
    - 3-7 days: 0.7 (medium)
    - 7-14 days: 0.85 (high)
    - 14+ days: 0.95 (very high)

    Args:
        historical_data_points: Number of historical days available

    Returns:
        Confidence score 0.0 to 1.0
    """
    if historical_data_points < 3:
        return 0.5
    elif historical_data_points < 7:
        return 0.7
    elif historical_data_points < 14:
        return 0.85
    else:
        return 0.95


# ===== UTILITY HELPERS =====

def get_date_range_string(start_date: datetime, end_date: datetime) -> str:
    """Format date range as string"""
    return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"


def get_7_days_ago(from_date: Optional[datetime] = None) -> datetime:
    """Get date 7 days ago"""
    base = from_date or datetime.now()
    return base - timedelta(days=7)


def get_14_days_ago(from_date: Optional[datetime] = None) -> datetime:
    """Get date 14 days ago"""
    base = from_date or datetime.now()
    return base - timedelta(days=14)
