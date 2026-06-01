# app/modules/tenants/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, URL, ValidationError, Regexp
from app.models.tenant import Tenant

class CreateTenantForm(FlaskForm):
    """Form to create a new journal / tenant"""

    name = StringField(
        'Journal Name',
        validators=[DataRequired(), Length(min=3, max=150)],
        render_kw={"placeholder": "e.g. Oxford Research Journal"}
    )

    subdomain = StringField(
        'Subdomain',
        validators=[
            DataRequired(),
            Length(min=3, max=50),
            Regexp(
                r'^[a-z0-9\-]+$',
                message='Only lowercase letters, numbers, and hyphens allowed'
            )
        ],
        render_kw={"placeholder": "e.g. oxford-research"}
    )

    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "Briefly describe your journal..."}
    )

    contact_email = StringField(
        'Contact Email',
        validators=[Optional(), Length(max=200)],
        render_kw={"placeholder": "editor@yourjournal.com"}
    )

    submit = SubmitField('Create Journal')

    def validate_subdomain(self, subdomain):
        """Check subdomain is not already taken"""
        existing = Tenant.query.filter_by(
            subdomain=subdomain.data.lower().strip()
        ).first()
        if existing:
            raise ValidationError(
                'This subdomain is already taken. Please choose another.'
            )

class UpdateTenantForm(FlaskForm):
    """Form to update tenant branding/settings"""

    name = StringField(
        'Journal Name',
        validators=[DataRequired(), Length(min=3, max=150)]
    )

    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=500)]
    )

    contact_email = StringField(
        'Contact Email',
        validators=[Optional(), Length(max=200)]
    )

    website_url = StringField(
        'Website URL',
        validators=[Optional(), Length(max=300)],
        render_kw={"placeholder": "https://yourjournal.com"}
    )

    primary_color = StringField(
        'Primary Color',
        validators=[Optional(), Length(max=10)],
        render_kw={"type": "color"}
    )

    secondary_color = StringField(
        'Secondary Color',
        validators=[Optional(), Length(max=10)],
        render_kw={"type": "color"}
    )

    footer_text = StringField(
        'Footer Text',
        validators=[Optional(), Length(max=300)],
        render_kw={"placeholder": "© 2025 Your Journal Name"}
    )

    submit = SubmitField('Save Changes')