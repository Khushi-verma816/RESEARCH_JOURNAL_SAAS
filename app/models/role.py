"""
Role Model - Role-Based Access Control (RBAC)
Manages user roles and permissions in the system
"""

from datetime import datetime

from app.core.extensions import db

class Role(db.Model):
    """Role model for implementing Role-Based Access Control."""

    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    permissions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Role {self.name}>'

    @staticmethod
    def insert_default_roles():
        """Insert default system roles."""
        roles = {
            'admin': {
                'description': 'Administrator with full system access',
                'permissions': 'all',
            },
            'editor': {
                'description': 'Editor with journal management access',
                'permissions': 'manage_journals,manage_reviews,edit_content',
            },
            'reviewer': {
                'description': 'Reviewer with peer review access',
                'permissions': 'review_submissions,view_manuscripts',
            },
            'author': {
                'description': 'Author with submission access',
                'permissions': 'submit_manuscripts,view_own_submissions',
            },
        }

        for role_name, role_data in roles.items():
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(
                    name=role_name,
                    description=role_data['description'],
                    permissions=role_data['permissions'],
                )
                db.session.add(role)
                print(f'  [OK] Created role: {role_name}')
            else:
                print(f'  [INFO] Role already exists: {role_name}')

        try:
            db.session.commit()
            print('[OK] Default roles setup complete')
        except Exception as e:
            db.session.rollback()
            print(f'[ERROR] Error creating roles: {e}')
            raise
