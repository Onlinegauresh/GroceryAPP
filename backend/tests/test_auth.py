"""Sample tests for authentication endpoints"""
import pytest
from fastapi.testclient import TestClient
from shared.models import Shop, User, RoleEnum
from shared.security import hash_password


def test_register_user(client, db_session):
    """Test user registration"""
    # Create a shop first
    shop = Shop(
        name="Test Shop",
        email="test@kirana.local",
        phone="9000000000",
        address="Test Address",
        city="Test City",
        state="Test State",
        pincode="100001"
    )
    db_session.add(shop)
    db_session.commit()
    db_session.refresh(shop)

    # Register user
    response = client.post(
        "/api/v1/auth/register",
        json={
            "shop_id": shop.id,
            "name": "Test User",
            "phone": "9876543210",
            "email": "user@test.local",
            "password": "secure123",
            "role": "customer"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["phone"] == "9876543210"
    assert data["role"] == "customer"
    assert "access_token" in data


def test_duplicate_registration(client, db_session):
    """Test registering same user twice"""
    shop = Shop(
        name="Test Shop",
        email="test2@kirana.local",
        phone="9000000001",
        address="Test Address",
        city="Test City",
        state="Test State",
        pincode="100002"
    )
    db_session.add(shop)
    db_session.commit()
    db_session.refresh(shop)

    # Register first user
    client.post(
        "/api/v1/auth/register",
        json={
            "shop_id": shop.id,
            "name": "User 1",
            "phone": "9876543220",
            "password": "pass123"
        }
    )

    # Try duplicate
    response = client.post(
        "/api/v1/auth/register",
        json={
            "shop_id": shop.id,
            "name": "User 2",
            "phone": "9876543220",
            "password": "pass123"
        }
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_login(client, db_session):
    """Test user login"""
    shop = Shop(
        name="Test Shop",
        email="test3@kirana.local",
        phone="9000000002",
        address="Test Address",
        city="Test City",
        state="Test State",
        pincode="100003"
    )
    db_session.add(shop)
    db_session.commit()
    db_session.refresh(shop)

    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "shop_id": shop.id,
            "name": "User Login",
            "phone": "9876543230",
            "password": "pass123"
        }
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "shop_id": shop.id,
            "phone": "9876543230",
            "password": "pass123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "customer"


def test_invalid_login(client, db_session):
    """Test login with wrong password"""
    shop = Shop(
        name="Test Shop",
        email="test4@kirana.local",
        phone="9000000003",
        address="Test Address",
        city="Test City",
        state="Test State",
        pincode="100004"
    )
    db_session.add(shop)
    db_session.commit()
    db_session.refresh(shop)

    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "shop_id": shop.id,
            "name": "User",
            "phone": "9876543240",
            "password": "pass123"
        }
    )

    # Try wrong password
    response = client.post(
        "/api/v1/auth/login",
        json={
            "shop_id": shop.id,
            "phone": "9876543240",
            "password": "wrongpass"
        }
    )

    assert response.status_code == 401
