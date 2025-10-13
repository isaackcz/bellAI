# 🔐 PepperAI Authentication System

## ✨ What's New

I've added a complete **login and dashboard system** to your PepperAI application! The design perfectly matches your existing Google Material-inspired UI with clean white backgrounds and indigo/purple accents.

## 🎨 New Pages

### 1. **Login Page** (`/login`)
![Login](https://img.shields.io/badge/Route-/login-blue)
- Email and password authentication
- "Remember me" checkbox (7-day session)
- Beautiful animated background with floating shapes
- Responsive design for mobile and desktop

### 2. **Registration Page** (`/register`)
![Register](https://img.shields.io/badge/Route-/register-green)
- User registration with validation
- Fields: Full Name, Username, Email, Password
- Password confirmation
- Automatic account creation

### 3. **Dashboard** (`/dashboard`)
![Dashboard](https://img.shields.io/badge/Route-/dashboard-purple)
- **Statistics Cards:**
  - Total Analyses
  - Bell Peppers Analyzed
  - Average Quality Score
  - User Account Info
- **Recent Analysis History** (last 10)
- Quick access to new analysis
- User profile display

### 4. **Analysis Page** (Updated)
![Analyze](https://img.shields.io/badge/Route-/analyze-orange)
- Now requires login
- Top navigation bar with Dashboard and Logout buttons
- All original functionality preserved

## 🚀 Quick Start

### Option 1: Using the Startup Script
```bash
start_pepperai.bat
```

### Option 2: Manual Start
```bash
# Install dependencies
pip install flask-sqlalchemy

# Run the app
python app.py
```

### Option 3: First Time Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Create admin account
python create_admin.py

# 3. Start the app
python app.py
```

## 📱 How to Use

1. **Open your browser** → `http://localhost:5000`

2. **Register a new account:**
   - Click "Register here"
   - Fill in your details
   - Click "Create Account"

3. **Login:**
   - Enter your email and password
   - Optionally check "Remember me"
   - Click "Login"

4. **Dashboard:**
   - View your statistics
   - See recent analyses
   - Click "New Analysis" to analyze bell peppers

5. **Analyze Bell Peppers:**
   - Use camera or upload images
   - Results are automatically saved to your history
   - Return to dashboard to view history

## 🔒 Security Features

✅ **Password Hashing** - Secure password storage using Werkzeug  
✅ **Session Management** - Flask sessions with configurable timeout  
✅ **Protected Routes** - Login required for analysis pages  
✅ **Input Validation** - Form validation for all user inputs  
✅ **CSRF Protection** - Built-in Flask session protection  

## 📊 Database

The system uses **SQLite** by default with two tables:

### Users Table
```sql
- id (Primary Key)
- username (Unique)
- email (Unique)
- password_hash
- full_name
- role (user/admin)
- created_at
- last_login
```

### Analysis History Table
```sql
- id (Primary Key)
- user_id (Foreign Key)
- image_path
- result_path
- peppers_found
- avg_quality
- analysis_data (JSON)
- created_at
```

## 🎨 UI Design Consistency

All new pages match your existing design:
- ✅ Google Material-inspired palette
- ✅ Indigo (#6366f1) and purple (#7c3aed) gradients
- ✅ Clean white backgrounds
- ✅ Smooth animations and transitions
- ✅ Floating shapes and grid patterns
- ✅ Inter font family
- ✅ Responsive design for all devices
- ✅ Consistent button styles and cards

## 🔧 Configuration

### Change Secret Key (Important for Production!)
In `app.py`, line 29:
```python
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
```

Change to a secure random string:
```python
import secrets
print(secrets.token_hex(32))  # Generate a secure key
```

### Session Timeout
In `app.py`, line 32:
```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
```

### Database (Optional - PostgreSQL for Production)
In `app.py`, line 30:
```python
# Current (Development)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pepperai.db'

# Production Example
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/pepperai'
```

## 📂 New Files Created

```
pepperai/
├── app.py (Updated - Authentication added)
├── requirements.txt (Updated - Flask-SQLAlchemy added)
├── templates/
│   ├── login.html (New)
│   ├── register.html (New)
│   ├── dashboard.html (New)
│   └── index.html (Updated - Navigation added)
├── pepperai.db (Auto-generated on first run)
├── start_pepperai.bat (New - Quick startup script)
├── create_admin.py (New - Admin account creator)
├── AUTH_SETUP.md (New - Detailed setup guide)
└── README_AUTH.md (This file)
```

## 🔑 Admin Account (Optional)

Create an admin account:
```bash
python create_admin.py
```

Default credentials:
- Email: `admin@pepperai.com`
- Password: `admin123`

**⚠️ Change the password after first login!**

## 🛠 Troubleshooting

### "Import flask_sqlalchemy could not be resolved"
```bash
pip install flask-sqlalchemy
```

### Database not created
```bash
# Delete existing database and restart
del pepperai.db
python app.py
```

### Session expired immediately
- Clear browser cookies for `localhost:5000`
- Or use incognito/private mode

### Port 5000 already in use
```bash
# Find and kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

## 🌟 Features Summary

| Feature | Status |
|---------|--------|
| User Registration | ✅ Complete |
| User Login | ✅ Complete |
| Dashboard with Stats | ✅ Complete |
| Analysis History | ✅ Complete |
| Password Hashing | ✅ Complete |
| Session Management | ✅ Complete |
| Protected Routes | ✅ Complete |
| Responsive Design | ✅ Complete |
| Matching UI Design | ✅ Complete |

## 📝 What Changed in Existing Files

### `app.py`
- ✅ Added Flask-SQLAlchemy
- ✅ Added User and AnalysisHistory models
- ✅ Added authentication routes (login, register, logout)
- ✅ Added dashboard route
- ✅ Added login_required decorators
- ✅ Analysis history auto-save

### `templates/index.html`
- ✅ Added top navigation bar
- ✅ Added Dashboard and Logout buttons
- ✅ All original functionality preserved

### `requirements.txt`
- ✅ Added `flask-sqlalchemy>=3.0.0`

## 🎯 Next Steps (Optional Enhancements)

1. **Password Reset** - Add "Forgot Password" functionality
2. **Email Verification** - Verify email addresses on registration
3. **User Profile** - Allow users to edit their profile
4. **Admin Panel** - Manage users and view all analyses
5. **Export Data** - Export analysis history to CSV/Excel
6. **Advanced Stats** - Charts and graphs for analysis trends
7. **API Keys** - Generate API keys for programmatic access
8. **Team Accounts** - Share analyses within teams

## 💡 Tips

- Use "Remember me" for convenient access
- Check the dashboard regularly for statistics
- Analysis history is automatically saved
- Use the navigation bar to switch between pages
- Logout when using shared computers

## 📞 Support

If you encounter any issues:
1. Check the console/terminal for error messages
2. Verify all dependencies are installed
3. Ensure Python 3.8+ is being used
4. Check that port 5000 is available
5. Review `AUTH_SETUP.md` for detailed troubleshooting

---

**Enjoy your new PepperAI authentication system!** 🌶️✨

Built with ❤️ using Flask, SQLAlchemy, and modern web design principles.

