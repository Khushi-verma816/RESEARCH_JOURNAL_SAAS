"""
Create all journal templates
"""
import os

def create_file(path, content):
    """Create a file with content"""
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created: {path}")

print("Creating journal templates...\n")

# Create templates directory
os.makedirs('app/templates/journal', exist_ok=True)

# view.html
create_file('app/templates/journal/view.html', '''{% extends "base.html" %}

{% block title %}{{ journal.name }} - Research Journal SaaS{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <h1 style="color: #007bff; margin-bottom: 10px;">{{ journal.name }}</h1>
    
    {% if journal.is_accepting_submissions %}
    <span style="background: #28a745; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">
        ✅ Accepting Submissions
    </span>
    {% else %}
    <span style="background: #dc3545; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">
        ❌ Not Accepting Submissions
    </span>
    {% endif %}
    
    {% if journal.description %}
    <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 6px;">
        <h3 style="color: #333; margin-top: 0;">About This Journal</h3>
        <p style="color: #666; line-height: 1.6;">{{ journal.description }}</p>
    </div>
    {% endif %}
    
    {% if journal.is_accepting_submissions %}
    <div style="margin: 20px 0;">
        <a href="{{ url_for('journal.submit', journal_id=journal.id) }}" 
           style="padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 6px; display: inline-block; font-size: 16px;">
            📄 Submit Manuscript
        </a>
    </div>
    {% endif %}
    
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
    
    <h2 style="color: #333; margin-bottom: 20px;">Recent Submissions</h2>
    
    {% if submissions %}
        <div style="display: grid; gap: 15px;">
            {% for submission in submissions %}
            <div style="border: 1px solid #ddd; padding: 15px; border-radius: 6px;">
                <h4 style="color: #333; margin: 0 0 10px 0;">{{ submission.title }}</h4>
                <p style="color: #666; font-size: 14px; margin: 5px 0;">
                    <strong>Author:</strong> {{ submission.author.full_name }}
                </p>
                <p style="color: #666; font-size: 14px; margin: 5px 0;">
                    <strong>Status:</strong> 
                    <span style="background: #007bff; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">
                        {{ submission.status|upper }}
                    </span>
                </p>
                <p style="color: #666; font-size: 14px; margin: 5px 0;">
                    <strong>Submitted:</strong> {{ submission.submitted_at.strftime('%B %d, %Y') }}
                </p>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <p style="color: #666; text-align: center; padding: 40px; background: #f8f9fa; border-radius: 6px;">
            No submissions yet.
        </p>
    {% endif %}
</div>
{% endblock %}
''')

# index.html
create_file('app/templates/journal/index.html', '''{% extends "base.html" %}

{% block title %}Journals - Research Journal SaaS{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
        <h1 style="color: #007bff; margin: 0;">📚 Journals</h1>
        {% if current_user.has_role('admin') or current_user.has_role('editor') %}
        <a href="{{ url_for('journal.create') }}" 
           style="padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 6px;">
            ➕ Create Journal
        </a>
        {% endif %}
    </div>

    {% if journals %}
        <div style="display: grid; gap: 20px;">
            {% for journal in journals %}
            <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
                <h3 style="color: #333; margin: 0 0 10px 0;">{{ journal.name }}</h3>
                <p style="color: #666; margin: 10px 0;">{{ journal.description or 'No description available' }}</p>
                
                <div style="margin-top: 15px; display: flex; gap: 10px;">
                    <a href="{{ url_for('journal.view', journal_id=journal.id) }}" 
                       style="padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; font-size: 14px;">
                        View Details
                    </a>
                    {% if journal.is_accepting_submissions %}
                    <a href="{{ url_for('journal.submit', journal_id=journal.id) }}" 
                       style="padding: 8px 16px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; font-size: 14px;">
                        Submit Manuscript
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <div style="text-align: center; padding: 40px; background: #f8f9fa; border-radius: 8px;">
            <p style="color: #666; font-size: 18px; margin-bottom: 20px;">No journals available yet.</p>
            {% if current_user.has_role('admin') or current_user.has_role('editor') %}
            <a href="{{ url_for('journal.create') }}" 
               style="padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 6px; display: inline-block;">
                Create Your First Journal
            </a>
            {% endif %}
        </div>
    {% endif %}
</div>
{% endblock %}
''')

# submit.html
create_file('app/templates/journal/submit.html', '''{% extends "base.html" %}

{% block title %}Submit to {{ journal.name }} - Research Journal SaaS{% endblock %}

{% block content %}
<div style="max-width: 800px; margin: 0 auto;">
    <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h1 style="color: #007bff; margin-bottom: 10px;">📄 Submit Manuscript</h1>
        <h3 style="color: #666; margin-bottom: 25px;">{{ journal.name }}</h3>
        
        <form method="POST">
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 8px; color: #333; font-weight: bold;">
                    Manuscript Title <span style="color: red;">*</span>
                </label>
                <input type="text" name="title" required
                       placeholder="Enter your manuscript title"
                       style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px;">
            </div>
            
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 8px; color: #333; font-weight: bold;">
                    Abstract <span style="color: red;">*</span>
                </label>
                <textarea name="abstract" rows="8" required
                          placeholder="Enter your abstract here (250-300 words recommended)"
                          style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; resize: vertical;"></textarea>
            </div>
            
            <div style="display: flex; gap: 10px;">
                <button type="submit" 
                        style="padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px;">
                    Submit Manuscript
                </button>
                <a href="{{ url_for('journal.view', journal_id=journal.id) }}" 
                   style="padding: 12px 24px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; font-size: 16px; display: inline-block;">
                    Cancel
                </a>
            </div>
        </form>
    </div>
</div>
{% endblock %}
''')

# my_submissions.html
create_file('app/templates/journal/my_submissions.html', '''{% extends "base.html" %}

{% block title %}My Submissions - Research Journal SaaS{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <h1 style="color: #007bff; margin-bottom: 25px;">📝 My Submissions</h1>
    
    {% if submissions %}
        <div style="display: grid; gap: 20px;">
            {% for submission in submissions %}
            <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
                <h3 style="color: #333; margin: 0 0 10px 0;">{{ submission.title }}</h3>
                
                <p style="color: #666; margin: 10px 0;">
                    <strong>Journal:</strong> {{ submission.journal.name }}
                </p>
                
                <p style="color: #666; margin: 10px 0;">
                    <strong>Status:</strong> 
                    <span style="background: #007bff; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">
                        {{ submission.status|upper }}
                    </span>
                </p>
                
                <p style="color: #666; margin: 10px 0;">
                    <strong>Submitted:</strong> {{ submission.submitted_at.strftime('%B %d, %Y at %I:%M %p') }}
                </p>
                
                <p style="color: #666; margin: 10px 0; line-height: 1.6;">
                    <strong>Abstract:</strong><br>
                    {{ submission.abstract[:200] }}{% if submission.abstract|length > 200 %}...{% endif %}
                </p>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <div style="text-align: center; padding: 60px; background: #f8f9fa; border-radius: 8px;">
            <p style="color: #666; font-size: 18px; margin-bottom: 20px;">You haven't submitted any manuscripts yet.</p>
            <a href="{{ url_for('journal.index') }}" 
               style="padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 6px; display: inline-block;">
                Browse Journals
            </a>
        </div>
    {% endif %}
</div>
{% endblock %}
''')

# view_submission.html
create_file('app/templates/journal/view_submission.html', '''{% extends "base.html" %}

{% block title %}{{ submission.title }} - Research Journal SaaS{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <h1 style="color: #007bff; margin-bottom: 20px;">{{ submission.title }}</h1>
    
    <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
        <p style="color: #666; margin: 5px 0;"><strong>Journal:</strong> {{ submission.journal.name }}</p>
        <p style="color: #666; margin: 5px 0;"><strong>Author:</strong> {{ submission.author.full_name }}</p>
        <p style="color: #666; margin: 5px 0;">
            <strong>Status:</strong> 
            <span style="background: #007bff; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">
                {{ submission.status|upper }}
            </span>
        </p>
        <p style="color: #666; margin: 5px 0;"><strong>Submitted:</strong> {{ submission.submitted_at.strftime('%B %d, %Y') }}</p>
    </div>
    
    <h3 style="color: #333; margin-top: 30px; margin-bottom: 15px;">Abstract</h3>
    <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; line-height: 1.6;">
        <p style="color: #333;">{{ submission.abstract }}</p>
    </div>
    
    <div style="margin-top: 30px;">
        <a href="{{ url_for('journal.my_submissions') }}" 
           style="padding: 10px 20px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; display: inline-block;">
            ← Back to My Submissions
        </a>
    </div>
</div>
{% endblock %}
''')

# my_reviews.html
create_file('app/templates/journal/my_reviews.html', '''{% extends "base.html" %}

{% block title %}My Reviews - Research Journal SaaS{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <h1 style="color: #007bff; margin-bottom: 25px;">✍️ My Reviews</h1>
    
    {% if reviews %}
        <div style="display: grid; gap: 20px;">
            {% for review in reviews %}
            <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
                <h3 style="color: #333; margin: 0 0 10px 0;">{{ review.submission.title }}</h3>
                <p style="color: #666; margin: 10px 0;"><strong>Journal:</strong> {{ review.submission.journal.name }}</p>
                <p style="color: #666; margin: 10px 0;">
                    <strong>Status:</strong> 
                    <span style="background: #6c757d; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">
                        {{ review.status|upper }}
                    </span>
                </p>
                <p style="color: #666; margin: 10px 0;"><strong>Assigned:</strong> {{ review.created_at.strftime('%B %d, %Y') }}</p>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <div style="text-align: center; padding: 60px; background: #f8f9fa; border-radius: 8px;">
            <p style="color: #666; font-size: 18px;">You have no review assignments yet.</p>
        </div>
    {% endif %}
</div>
{% endblock %}
''')

print("\n" + "="*60)
print("✅ ALL JOURNAL TEMPLATES CREATED SUCCESSFULLY!")
print("="*60)
print("\nRestart Flask and visit:")
print("  • http://localhost:5000/journal/")
print("  • http://localhost:5000/journal/3")