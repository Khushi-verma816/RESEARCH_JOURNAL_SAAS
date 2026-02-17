from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.blog import BlogPost
from app.models.journal import Submission

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/")
@login_required
def index():

    total_submissions = Submission.query.filter_by(
        user_id=current_user.id
    ).count()

    accepted = Submission.query.filter_by(
        user_id=current_user.id,
        status="accepted"
    ).count()

    rejected = Submission.query.filter_by(
        user_id=current_user.id,
        status="rejected"
    ).count()

    under_review = Submission.query.filter_by(
        user_id=current_user.id,
        status="under_review"
    ).count()

    blog_count = BlogPost.query.filter_by(
        author_id=current_user.id
    ).count()

    acceptance_rate = 0
    if total_submissions > 0:
        acceptance_rate = round(
            (accepted / total_submissions) * 100, 2
        )

    return render_template(
        "analytics/index.html",
        total_submissions=total_submissions,
        accepted=accepted,
        rejected=rejected,
        under_review=under_review,
        blog_count=blog_count,
        acceptance_rate=acceptance_rate
    )
