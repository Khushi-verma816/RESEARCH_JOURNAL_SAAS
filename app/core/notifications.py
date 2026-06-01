from datetime import datetime

from sqlalchemy.exc import OperationalError

from app.core.extensions import db
from app.models.notification import Notification
from app.models.user import User

PLATFORM_NOTIFICATION_ROLES = ('super_admin', 'admin')

def _ensure_notifications_table():
    Notification.__table__.create(bind=db.session.get_bind(), checkfirst=True)

def _with_table_retry(callback):
    try:
        return callback()
    except OperationalError as exc:
        details = str(exc).lower()
        if 'no such table' not in details or 'notification' not in details:
            raise
        db.session.rollback()
        _ensure_notifications_table()
        return callback()

def create_notifications_for_users(user_ids, title, message, link_url=None, category='general', commit=True):
    user_ids = [int(uid) for uid in user_ids if uid]
    if not user_ids:
        return 0

    def _create():
        rows = [
            Notification(
                user_id=uid,
                title=(title or '').strip()[:180] or 'Notification',
                message=(message or '').strip(),
                link_url=(link_url or '').strip() or None,
                category=category,
            )
            for uid in user_ids
        ]
        db.session.add_all(rows)
        if commit:
            db.session.commit()
        else:
            db.session.flush()
        return len(rows)

    return _with_table_retry(_create)

def create_notifications_for_roles(target_roles, title, message, link_url=None, category='general'):
    roles = {r for r in (target_roles or []) if r}
    if not roles:
        return 0

    query = User.query.filter_by(is_active=True)
    if 'all' not in roles:
        query = query.filter(User.role.in_(roles))

    user_ids = [u.id for u in query.all()]
    return create_notifications_for_users(
        user_ids=user_ids,
        title=title,
        message=message,
        link_url=link_url,
        category=category,
        commit=True,
    )

def notify_platform_admins(title, message, link_url=None, category='platform_event', exclude_user_ids=None):
    query = User.query.filter(User.role.in_(PLATFORM_NOTIFICATION_ROLES), User.is_active.is_(True))
    user_ids = [u.id for u in query.all()]
    excluded = {int(uid) for uid in (exclude_user_ids or []) if uid}
    if excluded:
        user_ids = [uid for uid in user_ids if uid not in excluded]
    return create_notifications_for_users(
        user_ids=user_ids,
        title=title,
        message=message,
        link_url=link_url,
        category=category,
        commit=True,
    )

def fetch_notifications_for_user(user_id, limit=12):
    def _fetch():
        return (
            Notification.query
            .filter_by(user_id=user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )

    return _with_table_retry(_fetch) or []

def count_unread_notifications(user_id):
    def _count():
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    return _with_table_retry(_count) or 0

def mark_notification_read(user_id, notification_id):
    def _mark():
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if not notification:
            return None
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
        return notification

    return _with_table_retry(_mark)

def mark_all_notifications_read_for_user(user_id):
    def _mark_all():
        pending = Notification.query.filter_by(user_id=user_id, is_read=False).all()
        now = datetime.utcnow()
        for row in pending:
            row.is_read = True
            row.read_at = now
        if pending:
            db.session.commit()
        return len(pending)

    return _with_table_retry(_mark_all) or 0
