"""AI router - REST API endpoints for AI features"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from shared.database import get_db
from app.auth.security import get_current_user
from shared.models import User, Shop

from .schemas import (
    ForecastResponse, ReorderResponse,
    LowStockRiskResponse, AnomalyDetectionResponse
)
from .service import (
    DemandForecastingService, ReorderSuggestionService,
    SmartLowStockAlertService, AnomalyDetectionService
)


router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI Intelligence"],
    dependencies=[Depends(get_current_user)]
)


async def verify_shop_access(
    shop_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """Verify user has access to shop"""
    shop = db.query(Shop).filter_by(id=shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # RBAC Rules:
    # - ADMIN: access to all shops
    # - OWNER: access to own shop only
    # - STAFF: access to own shop only (read-only)
    # - CUSTOMER: no access

    if current_user.role == "ADMIN":
        return True
    elif current_user.role in ["OWNER", "STAFF"]:
        # Check if user owns/manages this shop
        if current_user.shop_id == shop_id:
            return True
        else:
            raise HTTPException(
                status_code=403,
                detail="Access denied: You can only access your own shop"
            )
    else:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Your role cannot access AI features"
        )


# ===== DEMAND FORECASTING =====

@router.get(
    "/forecast/{shop_id}",
    response_model=ForecastResponse,
    summary="7-Day Demand Forecast",
    description="Generates 7-day demand forecast for all products using moving average and linear regression"
)
async def get_demand_forecast(
    shop_id: int,
    _: bool = Depends(lambda: verify_shop_access(shop_id)),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ForecastResponse:
    """
    Get 7-day demand forecast for all products in shop.

    **Algorithm:**
    1. Fetches last 14 days of sales data
    2. Calculates moving average (baseline)
    3. Applies linear regression for trend
    4. Generates 7-day forecast per product
    5. Assigns confidence based on data quality

    **Use Case:**
    - Plan purchasing for next week
    - Identify slow-moving vs. fast-moving items
    - Optimize stock levels

    **RBAC:** OWNER (own shop), ADMIN (all shops), STAFF (read-only, own shop)
    """
    service = DemandForecastingService(db)
    return service.forecast_all_products(shop_id)


# ===== REORDER SUGGESTIONS =====

@router.get(
    "/reorder-suggestions/{shop_id}",
    response_model=ReorderResponse,
    summary="Smart Reorder Suggestions",
    description="Suggests optimal reorder quantities based on stock velocity and forecast"
)
async def get_reorder_suggestions(
    shop_id: int,
    _: bool = Depends(lambda: verify_shop_access(shop_id)),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ReorderResponse:
    """
    Get reorder suggestions for all products.

    **Algorithm:**
    1. Calculates daily sales velocity (last 7 days)
    2. Gets 7-day demand forecast
    3. Computes optimal reorder quantity
    4. Marks urgent if stock < 3 days

    **Reorder Calculation:**
    - Safety Stock = (daily_velocity × lead_time) + 1
    - Reorder Point = safety_stock + (forecast_7day / 2)
    - Order Qty = (forecast_7day × 1.5) - current_stock
    - Returns 0 if already above reorder point

    **Use Case:**
    - Never run out of stock
    - Avoid overstocking
    - Optimize purchase orders

    **RBAC:** OWNER (own shop), ADMIN (all shops), STAFF (read-only, own shop)
    """
    service = ReorderSuggestionService(db)
    return service.get_reorder_suggestions(shop_id)


# ===== LOW STOCK RISK =====

@router.get(
    "/low-stock-risk/{shop_id}",
    response_model=LowStockRiskResponse,
    summary="Low Stock Risk Assessment",
    description="Identifies products at risk of stockout based on time-to-minimum"
)
async def get_low_stock_risk(
    shop_id: int,
    _: bool = Depends(lambda: verify_shop_access(shop_id)),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LowStockRiskResponse:
    """
    Assess low-stock risk for all products.

    **Algorithm:**
    1. Calculates daily velocity from recent sales
    2. Computes days until stock hits minimum level
    3. Classifies risk:
       - CRITICAL: < 1 day (stock will finish today/tomorrow)
       - HIGH: 1-3 days (order urgently)
       - MEDIUM: 3-7 days (plan reorder)
       - LOW: > 7 days (no action needed)

    **ASSUMPTION:** Risk is time-based, not just threshold.

    **Use Case:**
    - Identify critical shortages
    - Prevent stockouts
    - Prioritize purchasing

    **RBAC:** OWNER (own shop), ADMIN (all shops), STAFF (read-only, own shop)
    """
    service = SmartLowStockAlertService(db)
    return service.get_low_stock_risks(shop_id)


# ===== ANOMALY DETECTION =====

@router.get(
    "/anomalies/{shop_id}",
    response_model=AnomalyDetectionResponse,
    summary="Stock Anomaly Detection",
    description="Detects abnormal stock changes (shrinkage, theft, adjustments)"
)
async def detect_stock_anomalies(
    shop_id: int,
    days_back: int = Query(default=7, ge=1, le=30),
    _: bool = Depends(lambda: verify_shop_access(shop_id)),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AnomalyDetectionResponse:
    """
    Detect abnormal stock changes.

    **Algorithm:**
    1. Fetches sales data from last N days
    2. Calculates expected vs. actual stock change
    3. Flags deviations > 30% as anomalies
    4. Classifies by severity (LOW → CRITICAL)
    5. Suggests possible causes

    **Severity Levels:**
    - CRITICAL: Loss > 50% of sales (potential theft)
    - HIGH: Loss > 30% of sales (significant discrepancy)
    - MEDIUM: Loss > 10% of sales (minor inconsistency)
    - LOW: Normal variance

    **Possible Causes:**
    - Potential theft or shrinkage
    - Inventory damage or expiry
    - Unrecorded sales
    - Manual stock adjustments

    **Use Case:**
    - Detect inventory losses
    - Identify shrinkage issues
    - Monitor stock accuracy

    **Query Parameters:**
    - days_back: Period to analyze (1-30 days, default 7)

    **RBAC:** OWNER (own shop), ADMIN (all shops), STAFF (read-only, own shop)
    """
    service = AnomalyDetectionService(db)
    return service.detect_anomalies(shop_id, days_back=days_back)


# ===== HEALTH CHECK =====

@router.get(
    "/health",
    summary="AI Service Health Check",
    description="Simple health check endpoint"
)
async def health_check():
    """Health check - confirms AI service is running"""
    return {
        "status": "healthy",
        "service": "AI Intelligence",
        "features": [
            "demand_forecasting",
            "reorder_suggestions",
            "low_stock_risk",
            "anomaly_detection"
        ]
    }
