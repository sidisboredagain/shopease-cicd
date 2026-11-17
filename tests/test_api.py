"""Integration tests: call the Flask routes the same way a browser or client would."""

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    return app.test_client()


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_home_page_lists_products(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Wireless Mouse" in res.data


def test_home_page_search(client):
    res = client.get("/?q=shirt")
    assert b"Cotton T-Shirt" in res.data
    assert b"Wireless Mouse" not in res.data


def test_api_products(client):
    res = client.get("/api/products")
    assert res.status_code == 200
    assert len(res.get_json()) == 6


def test_api_products_by_category(client):
    data = client.get("/api/products?category=Fashion").get_json()
    assert [p["name"] for p in data] == ["Cotton T-Shirt"]


def test_api_single_product_and_404(client):
    assert client.get("/api/products/1").get_json()["name"] == "Wireless Mouse"
    assert client.get("/api/products/999").status_code == 404


def test_api_add_to_cart_and_view(client):
    res = client.post("/api/cart", json={"product_id": 1, "qty": 2})
    assert res.status_code == 201
    cart = client.get("/api/cart").get_json()
    assert cart["subtotal"] == 1198
    assert cart["total"] == 1198  # free delivery above 999


def test_api_add_out_of_stock_returns_400(client):
    res = client.post("/api/cart", json={"product_id": 6, "qty": 1})
    assert res.status_code == 400
    assert "stock" in res.get_json()["error"]


def test_api_bad_input_returns_400(client):
    res = client.post("/api/cart", json={"product_id": "abc"})
    assert res.status_code == 400


def test_api_remove_from_cart(client):
    client.post("/api/cart", json={"product_id": 3, "qty": 1})
    res = client.delete("/api/cart/3")
    assert res.status_code == 200
    assert res.get_json()["items"] == []
    assert client.delete("/api/cart/3").status_code == 404


def test_api_cart_with_coupon(client):
    client.post("/api/cart", json={"product_id": 2, "qty": 2})
    assert client.get("/api/cart?coupon=SAVE10").get_json()["total"] == 1618
    assert client.get("/api/cart?coupon=BAD").status_code == 400


def test_web_cart_flow(client):
    client.post("/cart/add/4")
    page = client.get("/cart")
    assert b"Steel Water Bottle" in page.data
    client.post("/cart/update/4", data={"qty": "3"})
    assert b"1047" in client.get("/cart").data  # 3 x 349
    client.post("/cart/remove/4")
    assert b"Your cart is empty" in client.get("/cart").data


def test_web_coupon_and_invalid_coupon(client):
    client.post("/cart/add/2")
    client.post("/cart/add/2")
    page = client.post("/cart", data={"coupon": "SAVE10"})
    assert b"1618" in page.data
    page = client.post("/cart", data={"coupon": "WRONG"})
    assert b"Invalid coupon code" in page.data


def test_web_out_of_stock_shows_message(client):
    res = client.post("/cart/add/6", follow_redirects=True)
    assert b"in stock" in res.data
