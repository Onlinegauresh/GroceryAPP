#!/usr/bin/env bash

# Quick start guide for SmartKirana AI Accounting System

# Test all 4 accounting endpoints in 5 minutes

echo "🎯 SmartKirana AI Accounting Module - Quick Start"
echo "=================================================="
echo ""

# Prerequisites

echo "📋 Prerequisites:"
echo " ✅ Server running on http://localhost:8000"
echo " ✅ Swagger UI: http://localhost:8000/api/docs"
echo " ✅ User with OWNER/ADMIN/STAFF role (JWT token)"
echo ""

# Step 1: Daily Sales Report

echo "STEP 1: Daily Sales Report"
echo "--------------------------"
echo "Endpoint: GET /api/v1/accounting/daily-sales/{shop_id}"
echo "Date: YYYY-MM-DD format"
echo ""
echo "CURL Example:"
echo " curl -X GET 'http://localhost:8000/api/v1/accounting/daily-sales/1?report_date=2024-01-15' \\"
echo " -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo " -H 'Content-Type: application/json'"
echo ""
echo "Response:"
echo " {\"shop_id\": 1, \"report_date\": \"2024-01-15\", \"total_orders\": 10, \"total_sales\": 5000.00, ...}"
echo ""

# Step 2: Profit & Loss

echo "STEP 2: Profit & Loss Report"
echo "----------------------------"
echo "Endpoint: GET /api/v1/accounting/profit-loss/{shop_id}"
echo "Period: YYYY-MM format (e.g., 2024-01)"
echo ""
echo "CURL Example:"
echo " curl -X GET 'http://localhost:8000/api/v1/accounting/profit-loss/1?period=2024-01' \\"
echo " -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo " -H 'Content-Type: application/json'"
echo ""
echo "Response:"
echo " {\"shop_id\": 1, \"gross_sales\": 50000, \"cost_of_goods_sold\": 30000, \"gross_profit\": 20000, ...}"
echo ""

# Step 3: Cash Book

echo "STEP 3: Cash Book"
echo "----------------"
echo "Endpoint: GET /api/v1/accounting/cash-book/{shop_id}"
echo "Period: from_date and to_date in YYYY-MM-DD format"
echo ""
echo "CURL Example:"
echo " curl -X GET 'http://localhost:8000/api/v1/accounting/cash-book/1?from_date=2024-01-01&to_date=2024-01-31' \\"
echo " -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo " -H 'Content-Type: application/json'"
echo ""
echo "Response:"
echo " {\"shop_id\": 1, \"opening_balance\": 1000, \"cash_in\": 5000, \"cash_out\": 2000, \"closing_balance\": 4000, ...}"
echo ""

# Step 4: Khata Statement

echo "STEP 4: Customer Khata Statement"
echo "-------------------------------"
echo "Endpoint: GET /api/v1/accounting/khata/{customer_id}"
echo "Query: shop_id (required for OWNER/STAFF/ADMIN)"
echo ""
echo "CURL Example:"
echo " curl -X GET 'http://localhost:8000/api/v1/accounting/khata/5?shop_id=1' \\"
echo " -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo " -H 'Content-Type: application/json'"
echo ""
echo "Response:"
echo " {\"customer_id\": 5, \"balance\": 1000.00, \"credit_limit\": 10000, \"available_credit\": 9000, ...}"
echo ""

echo "=================================================="
echo "✅ All 4 endpoints available!"
echo ""
echo "📚 For detailed documentation:"
echo " → Read ACCOUNTING_DOCUMENTATION.md"
echo " → Check Swagger UI: http://localhost:8000/api/docs"
echo ""
echo "🔐 RBAC Rules:"
echo " CUSTOMER: View own khata only"
echo " STAFF: Read-only reports for own shop"
echo " OWNER: Full access to own shop reports"
echo " ADMIN: Full access to all shops"
echo ""
