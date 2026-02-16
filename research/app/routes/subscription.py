from flask import Blueprint

subscription_bp = Blueprint("subscription", __name__)

@subscription_bp.route("/")
def subscription_home():
    return "Subscription working"
