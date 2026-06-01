from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.modules.video import video_bp
import random
import string

def generate_room_code(length=10):
    """Generate a random room code"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

@video_bp.route('/video')
@login_required
def index():
    return render_template('video/index.html', user=current_user)

@video_bp.route('/video/create', methods=['POST'])
@login_required
def create_room():
    room_name = request.form.get('room_name', '').strip()
    if not room_name:
        flash('Please enter a room name.', 'error')
        return redirect(url_for('video.index'))

    # Clean room name for URL
    room_code = room_name.lower().replace(' ', '-') + '-' + generate_room_code(5)
    return redirect(url_for('video.room', room_code=room_code, room_name=room_name))

@video_bp.route('/video/join', methods=['POST'])
@login_required
def join_room():
    room_code = request.form.get('room_code', '').strip()
    if not room_code:
        flash('Please enter a room code.', 'error')
        return redirect(url_for('video.index'))
    return redirect(url_for('video.room', room_code=room_code))

@video_bp.route('/video/room/<room_code>')
@login_required
def room(room_code):
    room_name = request.args.get('room_name', room_code)
    display_name = current_user.full_name
    return render_template('video/room.html',
        user=current_user,
        room_code=room_code,
        room_name=room_name,
        display_name=display_name
    )