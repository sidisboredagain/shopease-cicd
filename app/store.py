"""Business logic for the ShopEase store: product catalogue, cart and pricing.

This module has no Flask code, so it can be unit tested on its own.
"""

from dataclasses import dataclass

COUPONS = {"SAVE10": 10}  # coupon code -> percentage discount
FREE_DELIVERY_ABOVE = 999  # orders at or above this amount get free delivery
DELIVERY_CHARGE = 49
MAX_QTY_PER_ITEM = 10


@dataclass(frozen=True)
class Product:
    id: int
    name: str
    category: str
    price: int  # price in rupees
    stock: int


PRODUCTS = [
    Product(1, "Wireless Mouse", "Electronics", 599, 25),
    Product(2, "USB-C Charger 25W", "Electronics", 899, 15),
    Product(3, "Cotton T-Shirt", "Fashion", 449, 40),
    Product(4, "Steel Water Bottle", "Home", 349, 30),
    Product(5, "Notebook Pack (5)", "Stationery", 199, 60),
    Product(6, "Bluetooth Earbuds", "Electronics", 1499, 0),
]


class CartError(ValueError):
    """Raised when a cart operation breaks a business rule."""


def list_products(category=None, search=None):
    items = PRODUCTS
    if category:
        items = [p for p in items if p.category.lower() == category.lower()]
    if search:
        items = [p for p in items if search.lower() in p.name.lower()]
    return items


def get_product(product_id):
    for product in PRODUCTS:
        if product.id == product_id:
            return product
    return None


def add_to_cart(cart, product_id, qty=1):
    """Add qty of a product to the cart dict {product_id: qty}. Returns the cart."""
    product = get_product(product_id)
    if product is None:
        raise CartError("Product not found")
    if qty < 1:
        raise CartError("Quantity must be at least 1")
    new_qty = cart.get(product_id, 0) + qty
    if new_qty > product.stock:
        raise CartError(f"Only {product.stock} units of {product.name} in stock")
    if new_qty > MAX_QTY_PER_ITEM:
        raise CartError(f"Maximum {MAX_QTY_PER_ITEM} units per item")
    cart[product_id] = new_qty
    return cart


def update_quantity(cart, product_id, qty):
    if product_id not in cart:
        raise CartError("Product is not in the cart")
    if qty <= 0:
        cart.pop(product_id)
        return cart
    cart.pop(product_id)
    return add_to_cart(cart, product_id, qty)


def remove_from_cart(cart, product_id):
    if product_id not in cart:
        raise CartError("Product is not in the cart")
    cart.pop(product_id)
    return cart


def cart_summary(cart, coupon=None):
    """Return line items and the price breakdown for a cart."""
    lines = []
    subtotal = 0
    for product_id, qty in cart.items():
        product = get_product(product_id)
        if product is None:
            continue
        line_total = product.price * qty
        subtotal += line_total
        lines.append({"product_id": product.id, "name": product.name,
                      "price": product.price, "qty": qty,
                      "line_total": line_total})

    discount = 0
    if coupon:
        percent = COUPONS.get(coupon.upper())
        if percent is None:
            raise CartError("Invalid coupon code")
        discount = round(subtotal * percent / 100)

    after_discount = subtotal - discount
    if subtotal == 0 or after_discount >= FREE_DELIVERY_ABOVE:
        delivery = 0
    else:
        delivery = DELIVERY_CHARGE

    return {"items": lines, "subtotal": subtotal, "discount": discount,
            "delivery": delivery, "total": after_discount + delivery,
            "coupon": coupon.upper() if coupon else None}
