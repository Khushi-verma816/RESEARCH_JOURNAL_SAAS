from datetime import datetime

from app.core.extensions import db

class Testimonial(db.Model):
    __tablename__ = 'testimonials'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    designation = db.Column(db.String(150), nullable=True)
    organization = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    avatar_bg = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def initials(self):
        parts = [p.strip() for p in (self.name or '').split(' ') if p.strip()]
        if not parts:
            return 'RH'
        if len(parts) == 1:
            return parts[0][:2].upper()
        return f"{parts[0][0]}{parts[-1][0]}".upper()

    @property
    def role_line(self):
        segment = ', '.join(
            [x for x in [self.designation or '', self.organization or ''] if x]
        ).strip()
        return segment or 'Research Professional'
