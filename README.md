# DocuGen - Document Generation Application

A simple web application with user authentication for document generation.

## Features

- User registration and login
- Secure password hashing using Werkzeug
- Session-based authentication
- Clean and responsive UI
- SQLite database for user management

## Installation

1. Clone the repository:
```bash
git clone https://github.com/JwP-O7O/DocuGen.git
cd DocuGen
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

1. **Register**: Create a new account by visiting `/register`
2. **Login**: Sign in with your credentials at `/login`
3. **Dashboard**: Access your personalized dashboard after logging in
4. **Logout**: Sign out using the logout button in the navigation

## Security Features

- Password hashing with Werkzeug's `generate_password_hash`
- Session-based authentication
- Login required decorator for protected routes
- Input validation on registration and login forms
- CSRF protection through Flask's session management

## Configuration

The application uses environment variables for configuration:

- `SECRET_KEY`: Secret key for session management (defaults to 'dev-secret-key-change-in-production')

For production deployment, set a strong secret key:
```bash
export SECRET_KEY='your-secret-key-here'
```

## Database

The application uses SQLite with the following schema:

**Users Table:**
- `id`: Primary key
- `username`: Unique username (3+ characters)
- `email`: Unique email address
- `password_hash`: Hashed password

## Development

The application is built with:
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- Werkzeug 3.0.1

## Future Enhancements

- PDF document generation functionality
- Document templates
- User profile management
- Password reset functionality
- Email verification
- OAuth integration

## License

This project is provided as-is for educational and development purposes.
