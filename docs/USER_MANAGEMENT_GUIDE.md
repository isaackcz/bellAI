# User Management Guide

## Overview

PepperAI now includes a comprehensive user management system with role-based access control. This guide explains the new features and how to use them.

## User Roles

### Admin
- Full access to all features
- Can create, edit, and delete users
- Can view analytics for all users
- Has access to Settings page
- Can manage system configuration

### User
- Can analyze bell peppers
- Can view their own history and statistics
- Can export their own data
- Cannot access Settings page
- Cannot manage other users

## Authentication Changes

### Login Page
- No public registration link (removed)
- Users must contact administrator for account access
- Only login functionality is available

### User Creation
- Only administrators can create new users
- New users are created through Settings page
- Administrators can set initial passwords and roles

## Settings Page Features

### Access
- **URL:** `/settings`
- **Access Level:** Admin only
- **Navigation:** Visible in sidebar only for administrators

### System Statistics Dashboard
The settings page displays:
- Total Users count
- Total Administrators count
- Regular Users count
- Total Analyses (system-wide)
- Total Peppers Detected (system-wide)

### User Management

#### View Users
- Displays all users in a table format
- Shows user details: name, email, role
- Shows user activity: analyses, peppers, average quality
- Shows last login time

#### Create User
1. Click "Add New User" button
2. Fill in the form:
   - Full Name
   - Username (must be unique)
   - Email Address (must be unique)
   - Password (minimum 6 characters)
   - Role (User or Administrator)
3. Click "Save User"

#### Edit User
1. Click the edit (pencil) icon for a user
2. Modify any fields:
   - Full Name
   - Username
   - Email Address
   - Role
   - Password (leave empty to keep current)
3. Click "Save User"

#### Delete User
1. Click the delete (trash) icon for a user
2. Confirm the deletion
3. User and all their data will be permanently removed

**Note:** You cannot delete your own admin account or the last admin user.

#### View User Analytics
1. Click the chart icon for a user
2. View detailed analytics:
   - Quality distribution
   - Recent analyses
   - Monthly trends

## Security Features

### Role Protection
- Admins cannot demote themselves
- Cannot delete your own account
- Cannot delete the last admin user
- Password minimum length: 6 characters

### Session Management
- Sessions expire after 7 days (if "Remember me" is checked)
- Otherwise, sessions are temporary
- Secure password hashing using Werkzeug

## API Endpoints

### Settings Routes
All routes require admin authentication.

- `GET /settings/` - Settings page
- `POST /settings/users/create` - Create new user
- `GET /settings/users/<id>` - Get user details
- `PUT /settings/users/<id>/update` - Update user
- `DELETE /settings/users/<id>/delete` - Delete user
- `GET /settings/users/<id>/analytics` - Get user analytics

### Request/Response Format
All endpoints use JSON format:

```json
{
    "success": true,
    "message": "Operation completed",
    "data": {}
}
```

## Initial Setup

### Creating the First Admin User

Use the `create_admin.py` script:

```bash
python create_admin.py
```

This creates an admin account with:
- **Email:** admin@pepperai.com
- **Password:** admin123

**⚠️ IMPORTANT:** Change this password immediately after first login!

### Creating Additional Users

1. Login as admin
2. Navigate to Settings
3. Click "Add New User"
4. Fill in user details
5. Choose appropriate role
6. Save

## Best Practices

### For Administrators
1. Change default admin password immediately
2. Use strong passwords for all accounts
3. Regularly review user access
4. Monitor user analytics
5. Remove inactive users
6. Keep at least 2 admin users

### For Security
1. Don't share admin credentials
2. Use unique passwords for each user
3. Review user activity regularly
4. Remove terminated users promptly
5. Audit user roles periodically

## Troubleshooting

### Cannot Access Settings
- Verify you're logged in as admin
- Check session hasn't expired
- Clear browser cache and cookies

### Cannot Create User
- Check username isn't already taken
- Verify email isn't already registered
- Ensure password meets minimum length
- Confirm valid role selection

### Cannot Delete User
- You cannot delete yourself
- Cannot delete last admin user
- Verify you have admin privileges

## Database Schema

### User Model
```python
- id: Integer (Primary Key)
- username: String (Unique)
- email: String (Unique)
- password_hash: String
- full_name: String
- role: String ('user' or 'admin')
- created_at: DateTime
- last_login: DateTime
```

### Relationships
- User has many AnalysisHistory
- User has many BellPepperDetection
- Cascade delete removes user data

## Future Enhancements

Potential features for future versions:
- Password reset functionality
- Email verification
- Two-factor authentication
- User groups and permissions
- Audit logs
- Advanced analytics
- Bulk user operations
- CSV import/export
- User activity tracking
- Session management
- API key authentication

## Support

For issues or questions:
1. Check this documentation
2. Review error messages
3. Check application logs
4. Contact system administrator

