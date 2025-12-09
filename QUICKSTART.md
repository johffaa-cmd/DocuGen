# Quick Start Guide

## Getting Started with DocuGen

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/JwP-O7O/DocuGen.git
   cd DocuGen
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   # For development (with auto-reload)
   export FLASK_DEBUG=true
   python app.py
   ```
   
   The application will be available at `http://127.0.0.1:5000`

### First Time Setup

1. Open your browser and navigate to `http://127.0.0.1:5000`
2. Click "Register" to create a new account
3. Fill in your details:
   - Username (minimum 3 characters)
   - Email address
   - Password (minimum 6 characters)
   - Confirm password
4. Click "Register" to create your account
5. You'll be redirected to the login page
6. Enter your credentials and click "Login"
7. You're now logged in and can access your dashboard!

### Using the Application

**Home Page:** Welcome page with feature overview

**Register:** Create a new user account
- All fields are required
- Username must be unique
- Email must be unique
- Password must be at least 6 characters

**Login:** Sign in to your account
- Enter your username and password
- Click "Login" to access your dashboard

**Dashboard:** Your personal dashboard
- View your account information
- Access future document generation features

**Logout:** Sign out of your account
- Click "Logout" in the navigation menu
- You'll be redirected to the home page

### Troubleshooting

**Database Issues:**
If you encounter database errors, try resetting the database:
```bash
rm docugen.db
python app.py
```

**Port Already in Use:**
If port 5000 is already in use, specify a different port:
```bash
export FLASK_PORT=8000
python app.py
```

**Import Errors:**
Make sure all dependencies are installed:
```bash
pip install -r requirements.txt --upgrade
```

### Production Deployment

For production deployment:

1. Set required environment variables:
   ```bash
   export SECRET_KEY='your-strong-random-secret-key'
   export FLASK_DEBUG=false
   ```

2. Use a production WSGI server (e.g., Gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

### Support

For issues or questions:
- Check the [README.md](README.md) for detailed documentation
- Review the code comments in `app.py`
- Test your setup with `python test_auth.py`
