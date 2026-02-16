from flask import Blueprint

video_bp = Blueprint("video", __name__)

@video_bp.route("/")
def video_home():
    return "Video working"
