"""Web pages and REST API routes for ShopEase."""

from dataclasses import asdict

from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, session, url_for)

from . import store

bp = Blueprint("shop", __name__)


def _cart():
    # Flask sessions store JSON, so keys come back as strings
    return {int(k): v for k, v in session.get("cart", {}).items()}


def _save(cart):
    session["cart"] = {str(k): v for k, v in cart.items()}


# ---------- Health check (used by the pipeline smoke test) ----------

@bp.get("/health")
def health():
    return jsonify(status="ok", version=current_app.config["APP_VERSION"])


# ---------- Web pages ----------

@bp.get("/")
def index():
    search = request.args.get("q", "").strip()
    products = store.list_products(search=search or None)
    return render_template("index.html", products=products, search=search,
                           cart_count=sum(_cart().values()))


@bp.post("/cart/add/<int:product_id>")
def web_add(product_id):
    cart = _cart()
    try:
        store.add_to_cart(cart, product_id, 1)
        _save(cart)
        flash("Added to cart", "ok")
    except store.CartError as err:
        flash(str(err), "error")
    return redirect(request.referrer or url_for("shop.index"))


@bp.post("/cart/update/<int:product_id>")
def web_update(product_id):
    cart = _cart()
    try:
        store.update_quantity(cart, product_id, int(request.form.get("qty", 1)))
        _save(cart)
    except (store.CartError, ValueError) as err:
        flash(str(err), "error")
    return redirect(url_for("shop.cart_page"))


@bp.post("/cart/remove/<int:product_id>")
def web_remove(product_id):
    cart = _cart()
    try:
        store.remove_from_cart(cart, product_id)
        _save(cart)
    except store.CartError as err:
        flash(str(err), "error")
    return redirect(url_for("shop.cart_page"))


@bp.route("/cart", methods=["GET", "POST"])
def cart_page():
    if request.method == "POST":
        code = request.form.get("coupon", "").strip()
        session["coupon"] = code or None
    coupon = session.get("coupon")
    try:
        summary = store.cart_summary(_cart(), coupon)
    except store.CartError as err:
        flash(str(err), "error")
        session["coupon"] = None
        summary = store.cart_summary(_cart())
    return render_template("cart.html", s=summary,
                           cart_count=sum(_cart().values()))


# ---------- REST API ----------

@bp.get("/api/products")
def api_products():
    items = store.list_products(category=request.args.get("category"),
                                search=request.args.get("q"))
    return jsonify([asdict(p) for p in items])


@bp.get("/api/products/<int:product_id>")
def api_product(product_id):
    product = store.get_product(product_id)
    if product is None:
        return jsonify(error="Product not found"), 404
    return jsonify(asdict(product))


@bp.get("/api/cart")
def api_cart():
    try:
        return jsonify(store.cart_summary(_cart(), request.args.get("coupon")))
    except store.CartError as err:
        return jsonify(error=str(err)), 400


@bp.post("/api/cart")
def api_cart_add():
    data = request.get_json(silent=True) or {}
    cart = _cart()
    try:
        store.add_to_cart(cart, int(data.get("product_id", 0)),
                          int(data.get("qty", 1)))
    except (store.CartError, ValueError) as err:
        return jsonify(error=str(err)), 400
    _save(cart)
    return jsonify(store.cart_summary(cart)), 201


@bp.delete("/api/cart/<int:product_id>")
def api_cart_remove(product_id):
    cart = _cart()
    try:
        store.remove_from_cart(cart, product_id)
    except store.CartError as err:
        return jsonify(error=str(err)), 404
    _save(cart)
    return jsonify(store.cart_summary(cart))
