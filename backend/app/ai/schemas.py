"""AI schemas - Pydantic models for AI features"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from decimal import Decimal


# ===== DEMAND FORECASTING =====

class DailyForecast(BaseModel):
    """Daily demand forecast for a product"""
    date: str  # YYYY-MM-DD
    predicted_quantity: int
    confidence: float  # 0.0 to 1.0
    method: str  # "moving_average" or "linear_regression"


class ProductForecast(BaseModel):
    """7-day forecast for a single product"""
    product_id: int
    product_name: str
    forecast_period: str  # "2024-01-15 to 2024-01-22"
    current_stock: int
    historical_daily_avg: float
    forecasts: List[DailyForecast]
    total_predicted_7day: int


class ForecastResponse(BaseModel):
    """Complete forecast response for shop"""
    shop_id: int
    generated_at: datetime
    forecast_start_date: str
    total_products_forecasted: int
    products: List[ProductForecast]


# ===== REORDER SUGGESTIONS =====

class ReorderSuggestion(BaseModel):
    """Reorder suggestion for a product"""
    product_id: int
    product_name: str
    current_stock: int
    daily_sales_velocity: float  # units per day
    days_stock_left: float  # at current velocity
    forecasted_7day_demand: int
    suggested_reorder_qty: int
    urgent: bool  # True if stock < 3 days


class ReorderResponse(BaseModel):
    """Reorder suggestions for shop"""
    shop_id: int
    generated_at: datetime
    total_suggestions: int
    urgent_count: int
    suggestions: List[ReorderSuggestion]


# ===== LOW-STOCK RISK =====

class StockRisk(BaseModel):
    """Low-stock risk assessment"""
    product_id: int
    product_name: str
    current_stock: int
    min_stock_level: int
    daily_velocity: float
    days_until_minimum: float
    # "CRITICAL" (< 1 day), "HIGH" (1-3 days), "MEDIUM" (3-7 days), "LOW" (> 7 days)
    risk_level: str
    action_required: bool


class LowStockRiskResponse(BaseModel):
    """Low-stock risk for shop"""
    shop_id: int
    generated_at: datetime
    critical_count: int
    high_risk_count: int
    medium_risk_count: int
    risks: List[StockRisk]


# ===== ANOMALY DETECTION =====

class AnomalyEvent(BaseModel):
    """Detected anomalous event"""
    date: str  # YYYY-MM-DD
    product_id: int
    product_name: str
    expected_stock_change: int  # based on sales
    actual_stock_change: int  # what actually happened
    deviation: int  # actual - expected (loss)
    deviation_pct: float  # as percentage
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    # ["High sales", "Shrinkage", "Inventory adjustment", etc.]
    possible_causes: List[str]


class AnomalyDetectionResponse(BaseModel):
    """Anomalies detected in shop"""
    shop_id: int
    generated_at: datetime
    period: str  # "2024-01-15 to 2024-01-22"
    total_anomalies: int
    critical_anomalies: int
    total_loss_detected: Decimal
    anomalies: List[AnomalyEvent]


# ===== AI INSIGHTS SUMMARY =====

class AIInsightsSummary(BaseModel):
    """Quick summary of all AI insights"""
    shop_id: int
    generated_at: datetime

    # Forecast summary
    forecast_7day_total_demand: int

    # Reorder summary
    urgent_reorders: int
    total_reorder_qty: int

    # Risk summary
    critical_stock_items: int
    days_to_stockout: Optional[float]

    # Anomaly summary
    anomalies_detected: int
    estimated_loss: Decimal

    # Recommendations
    top_recommendation: str
