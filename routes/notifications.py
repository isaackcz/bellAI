"""
Notification routes for PepperAI
Handles notification management for admin and user notification display
"""
import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from functools import wraps
from werkzeug.utils import secure_filename
from models import db, User, Notification, NotificationAttachment, NotificationRead
from sqlalchemy import func

# Blueprint will be imported from routes.__init__
from routes import notifications_bp

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Configuration for file uploads
UPLOAD_FOLDER = 'notifications_files'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    """Determine file type based on extension"""
    if not filename:
        return 'other'
    
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']:
        return 'image'
    elif ext in ['pdf', 'doc', 'docx', 'txt', 'rtf']:
        return 'document'
    else:
        return 'other'

@notifications_bp.route('/admin/notifications')
@admin_required
def admin_notifications():
    """Admin page for managing notifications"""
    return render_template('notifications.html')

@notifications_bp.route('/api/notifications', methods=['GET'])
@admin_required
def get_notifications():
    """Get all notifications (admin view)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', 'all')  # all, active, draft, expired
    search = request.args.get('search', type=str)
    
    query = Notification.query.order_by(Notification.created_at.desc())
    
    # Filter by status
    if status == 'active':
        query = query.filter_by(is_active=True, is_draft=False)
    elif status == 'draft':
        query = query.filter_by(is_draft=True)
    elif status == 'expired':
        now = datetime.utcnow()
        query = query.filter(Notification.expires_at < now)

    # Filter by search term (title or message)
    if search:
        term = search.strip()
        if term:
            like_lower = f"%{term.lower()}%"
            query = query.filter(
                db.or_(
                    func.lower(Notification.title).like(like_lower),
                    func.lower(Notification.message).like(like_lower)
                )
            )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    notifications = [notif.to_dict() for notif in pagination.items]
    
    return jsonify({
        'notifications': notifications,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    })

@notifications_bp.route('/api/notifications/<int:notification_id>', methods=['GET'])
@admin_required
def get_notification(notification_id):
    """Get a single notification by id (admin view, for edit modal)"""
    notification = Notification.query.get_or_404(notification_id)
    return jsonify(notification.to_dict())

@notifications_bp.route('/api/notifications', methods=['POST'])
@admin_required
def create_notification():
    """Create a new notification"""
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('title') or not data.get('message'):
            return jsonify({'error': 'Title and message are required'}), 400
        
        # Create notification
        notification = Notification(
            title=data['title'],
            message=data['message'],
            sender_id=session['user_id'],
            recipient_type=data.get('recipient_type', 'all'),
            recipient_ids=json.dumps(data.get('recipient_ids', [])) if data.get('recipient_ids') else None,
            priority=data.get('priority', 'normal'),
            category=data.get('category', 'general'),
            scheduled_for=datetime.fromisoformat(data['scheduled_for']) if data.get('scheduled_for') else None,
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            is_draft=data.get('is_draft', False)
        )
        
        db.session.add(notification)
        db.session.flush()  # Get ID for attachments
        
        # Handle attachments if provided
        if data.get('attachment_ids'):
            for att_id in data['attachment_ids']:
                # Update attachment to link it to this notification
                attachment = NotificationAttachment.query.get(att_id)
                if attachment and attachment.notification_id is None:
                    attachment.notification_id = notification.id
        
        db.session.commit()
        
        return jsonify({
            'message': 'Notification created successfully',
            'notification': notification.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/notifications/<int:notification_id>', methods=['PUT'])
@admin_required
def update_notification(notification_id):
    """Update an existing notification"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            notification.title = data['title']
        if 'message' in data:
            notification.message = data['message']
        if 'recipient_type' in data:
            notification.recipient_type = data['recipient_type']
        if 'recipient_ids' in data:
            notification.recipient_ids = json.dumps(data['recipient_ids']) if data['recipient_ids'] else None
        if 'priority' in data:
            notification.priority = data['priority']
        if 'category' in data:
            notification.category = data['category']
        if 'scheduled_for' in data:
            notification.scheduled_for = datetime.fromisoformat(data['scheduled_for']) if data['scheduled_for'] else None
        if 'expires_at' in data:
            notification.expires_at = datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None
        if 'is_active' in data:
            notification.is_active = data['is_active']
        if 'is_draft' in data:
            notification.is_draft = data['is_draft']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Notification updated successfully',
            'notification': notification.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
@admin_required
def delete_notification(notification_id):
    """Delete a notification"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        # Delete associated files
        for attachment in notification.attachments:
            try:
                if os.path.exists(attachment.file_path):
                    os.remove(attachment.file_path)
            except:
                pass  # Continue even if file deletion fails
        
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({'message': 'Notification deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/notifications/upload', methods=['POST'])
@admin_required
def upload_file():
    """Upload file for notification attachment"""
    try:
        # Enforce max payload size when provided
        if request.content_length and request.content_length > MAX_FILE_SIZE:
            return jsonify({'error': 'File is too large (max 16MB)'}), 400
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Generate secure filename
        original_filename = file.filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{secure_filename(original_filename)}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save file
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_type = get_file_type(original_filename)
        
        # Create attachment record (not linked to notification yet)
        attachment = NotificationAttachment(
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type,
            file_type=file_type
        )
        
        db.session.add(attachment)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'attachment': attachment.to_dict()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/notifications/attachment/<int:attachment_id>')
@login_required
def download_attachment(attachment_id):
    """Download notification attachment"""
    attachment = NotificationAttachment.query.get_or_404(attachment_id)
    
    # Check if user has access to this notification
    if session.get('role') != 'admin':
        # Regular users can only access attachments from notifications sent to them
        notification = attachment.notification
        user_id = session['user_id']
        
        if user_id not in notification.get_recipient_list():
            return jsonify({'error': 'Access denied'}), 403
    
    return send_from_directory(
        os.path.dirname(attachment.file_path),
        os.path.basename(attachment.file_path),
        as_attachment=True,
        download_name=attachment.original_filename
    )

@notifications_bp.route('/api/notifications/users')
@admin_required
def get_users():
    """Get list of users for recipient selection"""
    users = User.query.filter_by(role='user').all()
    return jsonify([
        {
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'email': user.email
        }
        for user in users
    ])

# USER ROUTES (for reading notifications)

@notifications_bp.route('/api/user/notifications')
@login_required
def get_user_notifications():
    """Get notifications for current user"""
    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    # Get notifications for this user
    now = datetime.utcnow()
    
    # Base query for active notifications that haven't expired
    query = Notification.query.filter(
        Notification.is_active == True,
        Notification.is_draft == False,
        db.or_(
            Notification.expires_at.is_(None),
            Notification.expires_at > now
        )
    )
    
    # Filter notifications where user is recipient
    user_notifications = []
    for notification in query.all():
        if user_id in notification.get_recipient_list():
            user_notifications.append(notification)
    
    # Filter for unread only if requested
    if unread_only:
        user_notifications = [n for n in user_notifications if not n.is_read_by(user_id)]
    
    # Sort by created date (newest first)
    user_notifications.sort(key=lambda x: x.created_at, reverse=True)
    
    # Simple pagination
    start = (page - 1) * per_page
    end = start + per_page
    paginated_notifications = user_notifications[start:end]
    
    notifications_data = [notif.to_dict(user_id=user_id) for notif in paginated_notifications]
    
    return jsonify({
        'notifications': notifications_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': len(user_notifications),
            'pages': (len(user_notifications) + per_page - 1) // per_page,
            'has_prev': page > 1,
            'has_next': end < len(user_notifications)
        },
        'unread_count': len([n for n in user_notifications if not n.is_read_by(user_id)])
    })

@notifications_bp.route('/api/user/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read by current user"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        user_id = session['user_id']
        
        # Check if user has access to this notification
        if user_id not in notification.get_recipient_list():
            return jsonify({'error': 'Access denied'}), 403
        
        notification.mark_as_read(user_id)
        
        return jsonify({'message': 'Notification marked as read'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/user/notifications/unread-count')
@login_required
def get_unread_count():
    """Get count of unread notifications for current user"""
    user_id = session['user_id']
    now = datetime.utcnow()
    
    # Get all active notifications for this user
    query = Notification.query.filter(
        Notification.is_active == True,
        Notification.is_draft == False,
        db.or_(
            Notification.expires_at.is_(None),
            Notification.expires_at > now
        )
    )
    
    unread_count = 0
    for notification in query.all():
        if user_id in notification.get_recipient_list() and not notification.is_read_by(user_id):
            unread_count += 1
    
    return jsonify({'unread_count': unread_count})

@notifications_bp.route('/user-notifications')
@login_required
def user_notifications_page():
    """User notifications page"""
    return render_template('user_notifications.html')

@notifications_bp.route('/api/notifications/<int:notification_id>/stats')
@admin_required
def get_notification_stats(notification_id):
    """Get detailed stats for a notification"""
    notification = Notification.query.get_or_404(notification_id)
    
    # Get read receipts with user info
    read_receipts = db.session.query(NotificationRead, User).join(
        User, NotificationRead.user_id == User.id
    ).filter(NotificationRead.notification_id == notification_id).all()
    
    # Get all recipients
    recipient_ids = notification.get_recipient_list()
    all_recipients = User.query.filter(User.id.in_(recipient_ids)).all()
    
    # Build stats
    read_users = []
    unread_users = []
    
    read_user_ids = [receipt.user_id for receipt, _ in read_receipts]
    
    for user in all_recipients:
        if user.id in read_user_ids:
            # Find the read receipt for this user
            receipt = next((r for r, u in read_receipts if u.id == user.id), None)
            read_users.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'read_at': receipt.read_at.isoformat() if receipt else None
            })
        else:
            unread_users.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email
            })
    
    return jsonify({
        'notification': notification.to_dict(),
        'stats': {
            'total_recipients': len(all_recipients),
            'read_count': len(read_users),
            'unread_count': len(unread_users),
            'read_percentage': (len(read_users) / len(all_recipients)) * 100 if all_recipients else 0
        },
        'read_users': read_users,
        'unread_users': unread_users
    })
