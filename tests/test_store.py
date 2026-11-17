"""Unit tests for the business logic in app/store.py."""

import pytest

from app import store


def test_list_all_products():
    assert len(store.list_products()) == 6


def test_filter_by_category_is_case_insensitive():
    names = [p.name for p in store.list_products(category="electronics")]
    assert "Wireless Mouse" in names
    assert all(p.category == "Electronics" for p in store.list_products(category="ELECTRONICS"))


def test_search_by_name():
    result = store.list_products(search="bottle")
    assert [p.id for p in result] == [4]


def test_add_to_cart_new_item():
    cart = store.add_to_cart({}, 1, 2)
    assert cart == {1: 2}


def test_add_same_item_twice_increases_quantity():
    cart = store.add_to_cart({}, 3, 1)
    store.add_to_cart(cart, 3, 2)
    assert cart[3] == 3


def test_add_unknown_product_fails():
    with pytest.raises(store.CartError, match="not found"):
        store.add_to_cart({}, 999)


def test_add_out_of_stock_product_fails():
    with pytest.raises(store.CartError, match="in stock"):
        store.add_to_cart({}, 6)  # Bluetooth Earbuds have 0 stock


def test_quantity_limit_per_item():
    with pytest.raises(store.CartError, match="Maximum"):
        store.add_to_cart({}, 5, 11)


def test_zero_quantity_rejected():
    with pytest.raises(store.CartError):
        store.add_to_cart({}, 1, 0)


def test_update_quantity_to_zero_removes_item():
    cart = {1: 2}
    store.update_quantity(cart, 1, 0)
    assert cart == {}


def test_update_quantity_changes_value():
    cart = {1: 2}
    store.update_quantity(cart, 1, 4)
    assert cart == {1: 4}


def test_update_item_not_in_cart_fails():
    with pytest.raises(store.CartError):
        store.update_quantity({}, 1, 2)


def test_remove_from_cart():
    cart = {1: 1, 2: 1}
    store.remove_from_cart(cart, 1)
    assert cart == {2: 1}


def test_remove_missing_item_fails():
    with pytest.raises(store.CartError):
        store.remove_from_cart({}, 1)


def test_summary_small_order_pays_delivery():
    s = store.cart_summary({5: 1})  # 199
    assert s["subtotal"] == 199
    assert s["delivery"] == 49
    assert s["total"] == 248


def test_summary_large_order_gets_free_delivery():
    s = store.cart_summary({2: 2})  # 1798
    assert s["delivery"] == 0
    assert s["total"] == 1798


def test_coupon_applies_ten_percent():
    s = store.cart_summary({2: 2}, "save10")  # 1798 - 180
    assert s["discount"] == 180
    assert s["coupon"] == "SAVE10"
    assert s["total"] == 1618


def test_invalid_coupon_rejected():
    with pytest.raises(store.CartError, match="Invalid coupon"):
        store.cart_summary({1: 1}, "FREE100")


def test_empty_cart_summary():
    s = store.cart_summary({})
    assert s == {"items": [], "subtotal": 0, "discount": 0, "delivery": 0,
                 "total": 0, "coupon": None}
