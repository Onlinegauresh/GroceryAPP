"""AI service - Core business logic for all AI features"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from shared.models import (
    Order, OrderItem, Inventory, Product, Shop
)
from .schemas import (
    DailyForecast, ProductForecast, ForecastResponse,
    ReorderSuggestion, ReorderResponse,
    StockRisk, LowStockRiskResponse,
    AnomalyEvent, AnomalyDetectionResponse
)
from .utils import (
    calculate_moving_average, linear_regression_forecast,
    calculate_daily_velocity, calculate_days_stock_left,
    calculate_reorder_quantity, detect_stock_anomalies,
    get_anomaly_causes, classify_stock_risk, forecast_confidence,
    get_date_range_string, get_7_days_ago, get_14_days_ago
)


class DemandForecastingService:
    """Service for demand forecasting using moving average and linear regression"""

    def __init__(self, db: Session):
        self.db = db

    def get_product_forecast(self, product_id: int, shop_id: int) -> Optional[ProductForecast]:
        """
        Generate 7-day demand forecast for a product.

        Algorithm:
        1. Fetch last 7-14 days of sales data for product in this shop
        2. Calculate moving average (baseline)
        3. Apply linear regression for trend
        4. Generate 7-day forecast
        5. Calculate confidence based on data quality

        Returns: ProductForecast or None if insufficient data
        """
        # Get product details
        product = self.db.query(Product).filter_by(id=product_id).first()
        if not product:
            return None

        # Get current inventory for this shop
        inventory = self.db.query(Inventory).filter_by(
            product_id=product_id, shop_id=shop_id
        ).first()
        current_stock = inventory.quantity if inventory else 0

        # Fetch historical sales (last 14 days)
        two_weeks_ago = get_14_days_ago()
        daily_sales = self._get_daily_sales_by_product(
            product_id, shop_id, two_weeks_ago, datetime.now()
        )

        if not daily_sales:
            # No sales history - use stock buffer
            return ProductForecast(
                product_id=product_id,
                product_name=product.name,
                forecast_period=get_date_range_string(
                    datetime.now(), datetime.now() + timedelta(days=7)
                ),
                current_stock=current_stock,
                historical_daily_avg=0.0,
                forecasts=[
                    DailyForecast(
                        date=(datetime.now() + timedelta(days=i)
                              ).strftime('%Y-%m-%d'),
                        predicted_quantity=0,
                        confidence=0.5,
                        method="no_data"
                    )
                    for i in range(7)
                ],
                total_predicted_7day=0
            )

        # Calculate metrics
        daily_avg = calculate_moving_average(daily_sales, window=7)
        confidence = forecast_confidence(len(daily_sales))

        # Generate forecast using linear regression
        forecast_quantities = linear_regression_forecast(
            daily_sales, days_ahead=7)

        # Create daily forecasts
        forecasts = []
        today = datetime.now()
        for i, qty in enumerate(forecast_quantities):
            forecast_date = today + timedelta(days=i+1)
            forecasts.append(DailyForecast(
                date=forecast_date.strftime('%Y-%m-%d'),
                predicted_quantity=qty,
                confidence=confidence,
                method="linear_regression"
            ))

        return ProductForecast(
            product_id=product_id,
            product_name=product.name,
            forecast_period=get_date_range_string(
                today, today + timedelta(days=7)),
            current_stock=current_stock,
            historical_daily_avg=round(daily_avg, 2),
            forecasts=forecasts,
            total_predicted_7day=sum(forecast_quantities)
        )

    def forecast_all_products(self, shop_id: int) -> ForecastResponse:
        """Generate 7-day forecast for all active products in shop"""
        # Get all products sold in this shop (last 14 days)
        products = self.db.query(Product).join(
            OrderItem
        ).join(
            Order
        ).filter(
            Order.shop_id == shop_id,
            Order.order_date >= get_14_days_ago(),
            Order.order_status.in_(["DELIVERED", "PLACED"])
        ).distinct().all()

        forecasts = []
        for product in products:
            forecast = self.get_product_forecast(product.id, shop_id)
            if forecast:
                forecasts.append(forecast)

        return ForecastResponse(
            shop_id=shop_id,
            generated_at=datetime.now(),
            forecast_start_date=(
                datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            total_products_forecasted=len(forecasts),
            products=forecasts
        )

    def _get_daily_sales_by_product(
        self, product_id: int, shop_id: int,
        start_date: datetime, end_date: datetime
    ) -> List[int]:
        """
        Fetch daily sales quantities for a product in a shop.

        Returns list of quantities, one per day (ordered by date)
        """
        # Get all sales in date range
        sales_by_date = self.db.query(
            func.date(Order.order_date).label('sale_date'),
            func.sum(OrderItem.quantity).label('total_qty')
        ).join(
            OrderItem
        ).filter(
            OrderItem.product_id == product_id,
            Order.shop_id == shop_id,
            Order.order_date >= start_date,
            Order.order_date <= end_date,
            Order.order_status.in_(["DELIVERED", "PLACED"])
        ).group_by(
            func.date(Order.order_date)
        ).order_by(
            func.date(Order.order_date)
        ).all()

        # Fill missing dates with 0
        result = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        sales_dict = {row[0]: row[1] or 0 for row in sales_by_date}

        while current_date <= end_date_only:
            result.append(sales_dict.get(current_date, 0))
            current_date += timedelta(days=1)

        return result


class ReorderSuggestionService:
    """Service for generating reorder suggestions based on stock velocity"""

    def __init__(self, db: Session):
        self.db = db
        self.forecast_service = DemandForecastingService(db)

    def get_reorder_suggestions(self, shop_id: int) -> ReorderResponse:
        """
        Generate reorder suggestions for all products.

        Algorithm:
        1. For each product in shop:
           a. Get current stock
           b. Calculate daily sales velocity (last 7 days)
           c. Calculate days of stock left
           d. Get 7-day forecast
           e. Calculate optimal reorder quantity
           f. Mark as URGENT if stock < 3 days

        Returns: ReorderResponse with all suggestions
        """
        # Get all active products in shop
        products = self.db.query(Product).join(
            Inventory
        ).filter(
            Inventory.shop_id == shop_id
        ).all()

        suggestions = []
        urgent_count = 0

        for product in products:
            suggestion = self._suggest_reorder_for_product(product.id, shop_id)
            if suggestion:
                suggestions.append(suggestion)
                if suggestion.urgent:
                    urgent_count += 1

        # Sort by urgency
        suggestions.sort(key=lambda x: (not x.urgent, x.days_stock_left))

        return ReorderResponse(
            shop_id=shop_id,
            generated_at=datetime.now(),
            total_suggestions=len(suggestions),
            urgent_count=urgent_count,
            suggestions=suggestions
        )

    def _suggest_reorder_for_product(
        self, product_id: int, shop_id: int
    ) -> Optional[ReorderSuggestion]:
        """Generate reorder suggestion for single product"""
        # Get product and inventory
        inventory = self.db.query(Inventory).filter_by(
            product_id=product_id, shop_id=shop_id
        ).first()
        if not inventory:
            return None

        product = inventory.product
        current_stock = inventory.quantity

        # Calculate daily velocity (last 7 days)
        seven_days_ago = get_7_days_ago()
        daily_sales_by_date = self.db.query(
            func.sum(OrderItem.quantity).label('total_qty')
        ).join(
            Order
        ).filter(
            OrderItem.product_id == product_id,
            Order.shop_id == shop_id,
            Order.order_date >= seven_days_ago,
            Order.order_status.in_(["DELIVERED", "PLACED"])
        ).scalar() or 0

        daily_velocity = daily_sales_by_date / 7.0 if daily_sales_by_date > 0 else 0.0

        # Get 7-day forecast
        forecast = self.forecast_service.get_product_forecast(
            product_id, shop_id)
        forecasted_7day = forecast.total_predicted_7day if forecast else 0

        # Calculate stock left and reorder qty
        days_left = calculate_days_stock_left(current_stock, daily_velocity)
        reorder_qty = calculate_reorder_quantity(
            current_stock, daily_velocity, forecasted_7day, lead_time_days=1
        )

        # Mark urgent if < 3 days
        urgent = days_left < 3

        return ReorderSuggestion(
            product_id=product_id,
            product_name=product.name,
            current_stock=current_stock,
            daily_sales_velocity=round(daily_velocity, 2),
            days_stock_left=round(days_left, 1),
            forecasted_7day_demand=forecasted_7day,
            suggested_reorder_qty=reorder_qty,
            urgent=urgent
        )


class SmartLowStockAlertService:
    """Service for time-based low-stock alerts"""

    def __init__(self, db: Session):
        self.db = db

    def get_low_stock_risks(self, shop_id: int) -> LowStockRiskResponse:
        """
        Assess low-stock risk for all products.

        ASSUMPTION: Risk is based on time-to-minimum, not just threshold.

        Algorithm:
        1. For each product:
           a. Get current stock vs minimum
           b. Calculate daily velocity
           c. Calculate days until minimum at current velocity
           d. Classify risk level
           e. Mark if action required

        Returns: LowStockRiskResponse with risk assessments
        """
        inventories = self.db.query(Inventory).filter_by(shop_id=shop_id).all()

        risks = []
        critical_count = 0
        high_count = 0
        medium_count = 0

        for inventory in inventories:
            # Get daily velocity
            seven_days_ago = get_7_days_ago()
            daily_sales = self.db.query(
                func.sum(OrderItem.quantity).label('total_qty')
            ).join(
                Order
            ).filter(
                OrderItem.product_id == inventory.product_id,
                Order.shop_id == shop_id,
                Order.order_date >= seven_days_ago,
                Order.order_status.in_(["DELIVERED", "PLACED"])
            ).scalar() or 0

            daily_velocity = daily_sales / 7.0

            # Calculate days until minimum
            if daily_velocity > 0:
                stock_above_minimum = max(
                    0, inventory.quantity - inventory.min_quantity)
                days_until_min = stock_above_minimum / daily_velocity
            else:
                days_until_min = 999

            # Classify risk
            risk_level = classify_stock_risk(days_until_min)

            if risk_level == "CRITICAL":
                critical_count += 1
            elif risk_level == "HIGH":
                high_count += 1
            elif risk_level == "MEDIUM":
                medium_count += 1

            risk = StockRisk(
                product_id=inventory.product_id,
                product_name=inventory.product.name,
                current_stock=inventory.quantity,
                min_stock_level=inventory.min_quantity,
                daily_velocity=round(daily_velocity, 2),
                days_until_minimum=round(days_until_min, 1),
                risk_level=risk_level,
                action_required=risk_level in ["CRITICAL", "HIGH"]
            )
            risks.append(risk)

        # Sort by risk level
        risk_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        risks.sort(key=lambda x: risk_order[x.risk_level])

        return LowStockRiskResponse(
            shop_id=shop_id,
            generated_at=datetime.now(),
            critical_count=critical_count,
            high_risk_count=high_count,
            medium_risk_count=medium_count,
            risks=risks
        )


class AnomalyDetectionService:
    """Service for detecting abnormal stock changes"""

    def __init__(self, db: Session):
        self.db = db

    def detect_anomalies(
        self, shop_id: int, days_back: int = 7
    ) -> AnomalyDetectionResponse:
        """
        Detect stock anomalies (shrinkage, theft, adjustments).

        Algorithm:
        1. For last N days:
           a. Get expected stock change (sales recorded)
           b. Get actual stock change (from inventory snapshots or ledger)
           c. Calculate deviation
           d. Classify severity
           e. Suggest causes

        Currently using a simplified approach:
        - No inventory snapshots = use order data only
        - Flag large discrepancies vs. expected sales

        Returns: AnomalyDetectionResponse
        """
        anomalies = []
        today = datetime.now()
        period_start = today - timedelta(days=days_back)
        total_loss = Decimal('0')

        # Get all order items from period
        orders_in_period = self.db.query(Order).filter(
            Order.shop_id == shop_id,
            Order.order_date >= period_start,
            Order.order_status.in_(["DELIVERED", "PLACED"])
        ).all()

        # Group by product to find anomalies
        product_sales: Dict[int, int] = {}
        for order in orders_in_period:
            for item in order.order_items:
                product_sales[item.product_id] = product_sales.get(
                    item.product_id, 0) + item.quantity

        # For each product, check if expected matches actual
        # (Simplified: if no recent sales but stock missing = anomaly)
        for product_id, total_sales in product_sales.items():
            inventory = self.db.query(Inventory).filter_by(
                product_id=product_id, shop_id=shop_id
            ).first()

            if not inventory:
                continue

            product = inventory.product

            # Check for patterns
            daily_avg = total_sales / max(days_back, 1)

            # Get recent orders for this product
            recent_orders = [
                (o.order_date.date(), sum(
                    item.quantity for item in o.order_items
                    if item.product_id == product_id
                ))
                for o in orders_in_period
                if any(item.product_id == product_id for item in o.order_items)
            ]

            # Flag unusual days
            for order_date, daily_qty in recent_orders:
                # Check if spike or drought
                if daily_qty > daily_avg * 3:
                    # Unusual spike in sales
                    anomaly = AnomalyEvent(
                        date=str(order_date),
                        product_id=product_id,
                        product_name=product.name,
                        expected_stock_change=int(daily_avg),
                        actual_stock_change=daily_qty,
                        deviation=daily_qty - int(daily_avg),
                        deviation_pct=((daily_qty - daily_avg) /
                                       max(daily_avg, 1)) * 100,
                        severity="MEDIUM",
                        possible_causes=["Bulk order",
                                         "High demand day", "Promotional sales"]
                    )
                    anomalies.append(anomaly)

        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        anomalies.sort(key=lambda x: severity_order[x.severity])

        critical_count = sum(1 for a in anomalies if a.severity == "CRITICAL")

        return AnomalyDetectionResponse(
            shop_id=shop_id,
            generated_at=datetime.now(),
            period=get_date_range_string(period_start, today),
            total_anomalies=len(anomalies),
            critical_anomalies=critical_count,
            total_loss_detected=total_loss,
            anomalies=anomalies
        )
