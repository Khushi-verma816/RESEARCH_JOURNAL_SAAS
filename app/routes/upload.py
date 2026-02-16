"""
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
