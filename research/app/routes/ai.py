from flask import Blueprint

ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/")
def ai_home():
    return "AI working"
