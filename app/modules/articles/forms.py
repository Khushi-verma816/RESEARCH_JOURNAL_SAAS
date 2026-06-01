# app/modules/articles/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

CATEGORIES = [
    ('', 'Select a category...'),
    ('computer_science',    'Computer Science'),
    ('medicine',            'Medicine & Health'),
    ('physics',             'Physics'),
    ('chemistry',           'Chemistry'),
    ('biology',             'Biology'),
    ('mathematics',         'Mathematics'),
    ('engineering',         'Engineering'),
    ('social_science',      'Social Sciences'),
    ('economics',           'Economics'),
    ('psychology',          'Psychology'),
    ('environmental',       'Environmental Science'),
    ('other',               'Other'),
]

class SubmitArticleForm(FlaskForm):

    title = StringField(
        'Article Title',
        validators=[DataRequired(), Length(min=10, max=500)],
        render_kw={"placeholder": "Enter the full title of your article"}
    )

    abstract = TextAreaField(
        'Abstract',
        validators=[DataRequired(), Length(min=100, max=3000)],
        render_kw={"placeholder": "Write a clear summary of your research (100-3000 characters)..."}
    )

    keywords = StringField(
        'Keywords',
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "e.g. machine learning, neural networks, deep learning"}
    )

    category = SelectField(
        'Research Category',
        choices=CATEGORIES,
        validators=[DataRequired()]
    )

    co_authors = StringField(
        'Co-Authors',
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "e.g. Dr. Smith, Prof. Jones (comma separated)"}
    )

    content = TextAreaField(
        'Full Article Content',
        validators=[Optional()],
        render_kw={"placeholder": "Paste your full article content here (optional if uploading PDF)..."}
    )

    submit = SubmitField('Submit Article')
    save_draft = SubmitField('Save as Draft')

class ReviewArticleForm(FlaskForm):

    review_notes = TextAreaField(
        'Review Comments',
        validators=[DataRequired(), Length(min=20, max=5000)],
        render_kw={"placeholder": "Write detailed review comments for the author..."}
    )

    decision = SelectField(
        'Decision',
        choices=[
            ('',                'Select decision...'),
            ('accept',          'Accept'),
            ('minor_revision',  'Minor Revision Required'),
            ('major_revision',  'Major Revision Required'),
            ('reject',          'Reject'),
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField('Submit Review')

class EditorDecisionForm(FlaskForm):

    editor_notes = TextAreaField(
        'Editor Notes',
        validators=[Optional(), Length(max=3000)],
        render_kw={"placeholder": "Add notes for the author (optional)..."}
    )

    decision = SelectField(
        'Final Decision',
        choices=[
            ('',          'Select decision...'),
            ('publish',   'Publish Now'),
            ('accept',    'Accept (pending final check)'),
            ('reject',    'Reject'),
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField('Submit Decision')