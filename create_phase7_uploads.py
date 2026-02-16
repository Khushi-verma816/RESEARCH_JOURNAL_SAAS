"""
Phase 7: File Upload System
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

files = {
    'app/routes/upload.py': '''"""
File upload routes
"""
from flask import Blueprint, request, jsonify, send_from_directory, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from app.extensions import db
from app.models import Submission

upload_bp = Blueprint('upload', __name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'manuscripts'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'profiles'), exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    """Get file size"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size

@upload_bp.route('/manuscript/<int:submission_id>', methods=['POST'])
@login_required
def upload_manuscript(submission_id):
    """Upload manuscript file for a submission"""
    submission = Submission.query.get_or_404(submission_id)
    
    # Check ownership
    if submission.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Use PDF, DOCX, DOC, or TXT'}), 400
    
    # Check file size
    if get_file_size(file) > MAX_FILE_SIZE:
        return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
    
    # Generate unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = secure_filename(file.filename)
    unique_filename = f"{submission_id}_{timestamp}_{filename}"
    
    # Save file
    filepath = os.path.join(UPLOAD_FOLDER, 'manuscripts', unique_filename)
    file.save(filepath)
    
    # Update submission
    submission.manuscript_file_url = unique_filename
    db.session.commit()
    
    return jsonify({
        'success': True,
        'filename': filename,
        'url': url_for('upload.download_manuscript', filename=unique_filename)
    })

@upload_bp.route('/download/manuscript/<filename>')
@login_required
def download_manuscript(filename):
    """Download a manuscript file"""
    # Security: verify user has access to this file
    submission = Submission.query.filter_by(manuscript_file_url=filename).first_or_404()
    
    # Check access
    can_access = (
        submission.user_id == current_user.id or
        current_user.has_role('admin') or
        current_user.has_role('editor')
    )
    
    if not can_access:
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    return send_from_directory(
        os.path.join(UPLOAD_FOLDER, 'manuscripts'),
        filename,
        as_attachment=True
    )

@upload_bp.route('/profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    """Upload user profile picture"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Only allow images
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        return jsonify({'error': 'Only PNG, JPG, and JPEG images allowed'}), 400
    
    # Check file size (max 5MB for images)
    if get_file_size(file) > 5 * 1024 * 1024:
        return jsonify({'error': 'Image too large. Maximum size is 5MB'}), 400
    
    # Generate unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"user_{current_user.id}_{timestamp}.{ext}"
    
    # Save file
    filepath = os.path.join(UPLOAD_FOLDER, 'profiles', unique_filename)
    file.save(filepath)
    
    # Update user profile (you'll need to add profile_picture field to User model)
    # current_user.profile_picture = unique_filename
    # db.session.commit()
    
    return jsonify({
        'success': True,
        'filename': unique_filename,
        'url': url_for('upload.get_profile_picture', filename=unique_filename)
    })

@upload_bp.route('/profile/<filename>')
def get_profile_picture(filename):
    """Get profile picture"""
    return send_from_directory(
        os.path.join(UPLOAD_FOLDER, 'profiles'),
        filename
    )
''',

    'app/templates/journal/submit_with_upload.html': '''{% extends "base.html" %}

{% block title %}Submit to {{ journal.name }} - Research Journal SaaS{% endblock %}

{% block content %}
<div style="max-width: 800px; margin: 0 auto;">
    <div style="background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h1 style="color: #007bff; margin-bottom: 10px;">📄 Submit Manuscript</h1>
        <h3 style="color: #666; margin-bottom: 25px;">{{ journal.name }}</h3>
        
        <form method="POST" id="submissionForm">
            <!-- Title -->
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 8px; color: #333; font-weight: bold;">
                    Manuscript Title <span style="color: red;">*</span>
                </label>
                <input type="text" name="title" id="title" required
                       placeholder="Enter your manuscript title"
                       style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px;">
            </div>
            
            <!-- Abstract -->
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 8px; color: #333; font-weight: bold;">
                    Abstract <span style="color: red;">*</span>
                </label>
                <textarea name="abstract" id="abstract" rows="8" required
                          placeholder="Enter your abstract here (250-300 words recommended)"
                          style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; resize: vertical;"></textarea>
            </div>
            
            <!-- File Upload -->
            <div style="margin-bottom: 25px;">
                <label style="display: block; margin-bottom: 8px; color: #333; font-weight: bold;">
                    Manuscript File <span style="color: red;">*</span>
                </label>
                <div style="border: 2px dashed #ddd; border-radius: 6px; padding: 30px; text-align: center; background: #f8f9fa;">
                    <input type="file" id="fileInput" accept=".pdf,.docx,.doc,.txt" required
                           style="display: none;" onchange="handleFileSelect(event)">
                    <button type="button" onclick="document.getElementById('fileInput').click()"
                            style="padding: 12px 24px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin-bottom: 10px;">
                        📎 Choose File
                    </button>
                    <p style="color: #666; margin: 10px 0; font-size: 14px;">
                        Accepted formats: PDF, DOCX, DOC, TXT (Max 16MB)
                    </p>
                    <div id="fileInfo" style="margin-top: 15px; padding: 10px; background: white; border-radius: 4px; display: none;">
                        <p style="color: #333; margin: 0;"><strong>Selected:</strong> <span id="fileName"></span></p>
                        <p style="color: #666; margin: 5px 0 0 0; font-size: 13px;"><span id="fileSize"></span></p>
                    </div>
                </div>
            </div>
            
            <!-- Buttons -->
            <div style="display: flex; gap: 10px;">
                <button type="submit" id="submitBtn"
                        style="padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px;">
                    Submit Manuscript
                </button>
                <a href="{{ url_for('journal.view', journal_id=journal.id) }}" 
                   style="padding: 12px 24px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; font-size: 16px; display: inline-block;">
                    Cancel
                </a>
            </div>
            
            <!-- Progress -->
            <div id="uploadProgress" style="display: none; margin-top: 20px;">
                <div style="background: #e9ecef; border-radius: 4px; height: 30px; overflow: hidden;">
                    <div id="progressBar" style="background: #28a745; height: 100%; width: 0%; transition: width 0.3s; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                        0%
                    </div>
                </div>
                <p id="uploadStatus" style="text-align: center; color: #666; margin-top: 10px;"></p>
            </div>
        </form>
    </div>
</div>

<script>
let selectedFile = null;

function handleFileSelect(event) {
    selectedFile = event.target.files[0];
    
    if (selectedFile) {
        // Display file info
        document.getElementById('fileName').textContent = selectedFile.name;
        document.getElementById('fileSize').textContent = formatFileSize(selectedFile.size);
        document.getElementById('fileInfo').style.display = 'block';
    }
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' bytes';
    else if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

document.getElementById('submissionForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!selectedFile) {
        alert('Please select a file to upload');
        return;
    }
    
    const submitBtn = document.getElementById('submitBtn');
    const progressDiv = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const uploadStatus = document.getElementById('uploadStatus');
    
    // Disable button
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    progressDiv.style.display = 'block';
    
    try {
        // Step 1: Create submission
        uploadStatus.textContent = 'Creating submission...';
        progressBar.style.width = '30%';
        progressBar.textContent = '30%';
        
        const formData = new FormData();
        formData.append('title', document.getElementById('title').value);
        formData.append('abstract', document.getElementById('abstract').value);
        
        const submitResponse = await fetch(window.location.href, {
            method: 'POST',
            body: formData
        });
        
        if (!submitResponse.ok) {
            throw new Error('Failed to create submission');
        }
        
        // Get submission ID from redirect URL or response
        const submissionId = await submitResponse.text();
        const submissionIdMatch = submissionId.match(/submission\\/view\\/(\\d+)/);
        
        if (!submissionIdMatch) {
            // Form submission successful, redirect
            window.location.href = '{{ url_for("journal.my_submissions") }}';
            return;
        }
        
        // Step 2: Upload file
        uploadStatus.textContent = 'Uploading manuscript...';
        progressBar.style.width = '60%';
        progressBar.textContent = '60%';
        
        const fileData = new FormData();
        fileData.append('file', selectedFile);
        
        const uploadResponse = await fetch(`/upload/manuscript/${submissionIdMatch[1]}`, {
            method: 'POST',
            body: fileData
        });
        
        const uploadResult = await uploadResponse.json();
        
        if (!uploadResult.success) {
            throw new Error(uploadResult.error || 'Upload failed');
        }
        
        // Success
        progressBar.style.width = '100%';
        progressBar.textContent = '100%';
        uploadStatus.textContent = 'Success! Redirecting...';
        
        setTimeout(() => {
            window.location.href = '{{ url_for("journal.my_submissions") }}';
        }, 1000);
        
    } catch (error) {
        alert('Error: ' + error.message);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Manuscript';
        progressDiv.style.display = 'none';
    }
});
</script>
{% endblock %}
''',

    'app/templates/journal/view_submission_with_download.html': '''{% extends "base.html" %}

{% block title %}{{ submission.title }} - Research Journal SaaS{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <h1 style="color: #007bff; margin-bottom: 20px;">{{ submission.title }}</h1>
    
    <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
        <p style="color: #666; margin: 5px 0;"><strong>Journal:</strong> {{ submission.journal.name }}</p>
        <p style="color: #666; margin: 5px 0;"><strong>Author:</strong> {{ submission.author.full_name }}</p>
        <p style="color: #666; margin: 5px 0;">
            <strong>Status:</strong> 
            {% if submission.status == 'submitted' %}
                <span style="background: #007bff; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">SUBMITTED</span>
            {% elif submission.status == 'under_review' %}
                <span style="background: #ffc107; color: #333; padding: 4px 12px; border-radius: 12px; font-size: 12px;">UNDER REVIEW</span>
            {% elif submission.status == 'accepted' %}
                <span style="background: #28a745; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">ACCEPTED</span>
            {% elif submission.status == 'rejected' %}
                <span style="background: #dc3545; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">REJECTED</span>
            {% endif %}
        </p>
        <p style="color: #666; margin: 5px 0;"><strong>Submitted:</strong> {{ submission.submitted_at.strftime('%B %d, %Y') }}</p>
        
        <!-- Download Manuscript -->
        {% if submission.manuscript_file_url and submission.manuscript_file_url != 'placeholder.pdf' %}
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #ddd;">
            <p style="color: #333; margin: 0 0 10px 0;"><strong>📎 Manuscript File:</strong></p>
            <a href="{{ url_for('upload.download_manuscript', filename=submission.manuscript_file_url) }}" 
               style="padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; display: inline-block;">
                📥 Download Manuscript
            </a>
        </div>
        {% endif %}
    </div>
    
    <h3 style="color: #333; margin-top: 30px; margin-bottom: 15px;">Abstract</h3>
    <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; line-height: 1.6;">
        <p style="color: #333;">{{ submission.abstract }}</p>
    </div>
    
    <!-- Reviews Section -->
    {% if reviews %}
    <h3 style="color: #333; margin-top: 30px; margin-bottom: 15px;">Reviews</h3>
    <div style="display: grid; gap: 15px;">
        {% for review in reviews %}
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 6px;">
            <p style="margin: 5px 0;"><strong>Reviewer:</strong> {{ review.reviewer.full_name }}</p>
            <p style="margin: 5px 0;">
                <strong>Status:</strong> 
                <span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">
                    {{ review.status|upper }}
                </span>
            </p>
            {% if review.comments %}
            <p style="margin: 10px 0 5px 0;"><strong>Comments:</strong></p>
            <p style="color: #666;">{{ review.comments }}</p>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <div style="margin-top: 30px;">
        <a href="{{ url_for('journal.my_submissions') }}" 
           style="padding: 10px 20px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; display: inline-block;">
            ← Back to My Submissions
        </a>
    </div>
</div>
{% endblock %}
''',
}

print("Creating Phase 7 files...\n")
for filepath, content in files.items():
    create_file(filepath, content)

# Create uploads directory
os.makedirs('uploads/manuscripts', exist_ok=True)
os.makedirs('uploads/profiles', exist_ok=True)
print("✅ Created: uploads/manuscripts/")
print("✅ Created: uploads/profiles/")

print("\n" + "="*60)
print("✅ PHASE 7 FILES CREATED SUCCESSFULLY!")
print("="*60)
print("\nNext steps:")
print("1. Update app/__init__.py to register upload blueprint")
print("2. Update journal.py routes to use new templates")
print("3. Restart Flask")
print("4. Test file uploads!")