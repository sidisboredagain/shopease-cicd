"""ShopEase - a small online shopping application used to demonstrate CI/CD."""

import os

from flask import Flask

__version__ = "1.0.0"


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
    app.config["APP_VERSION"] = os.environ.get("APP_VERSION", __version__)
    if test_config:
        app.config.update(test_config)

    from .routes import bp
    app.register_blueprint(bp)
    return app
