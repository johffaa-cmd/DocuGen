## Analysis of the provided Python code

### What does this code do?
- CLI tool that asks for transaction data or partially reads it from a PDF.
- Builds a `Transaction` object, determines the bank profile (ING/Rabobank/ABN), generates a reference, and formats IBAN/amount.
- Generates a PDF with ReportLab (`PDFEngine`): header with logo/colors, status block, detail table, SEPA QR code, and footer.
- Optionally scans an existing PDF (with `pypdf`) to extract amount, IBAN, name, and description.

### What can it do (use cases)?
- Quickly create a “transaction confirmation” PDF with bank colors and a QR to validate data.
- Automatically copy data from a booking/invoice PDF to reduce manual entry.

### Improvements (compact and feasible)
- **Validation and errors**
  - Implement or improve an IBAN regex (ISO 13616, length + mod-97 check).
  - Check negative/unparsed amounts and missing fields.
  - Catch specific exceptions (e.g., `PdfReaderError`/`PdfReadWarning`, `ValueError`) and return clear messages instead of `except: pass`.
- **References**
  - For security: use `secrets`/`uuid` so references are not predictable.
  - For deterministic tests: inject a seeded `random.Random`.
  - Choose deliberately per use case (production vs tests).
- **Scanner robustness**
  - Catch specific `PdfReader` exceptions.
  - Strip unusual whitespace.
  - Support multiple currencies/amount formats via `Decimal` (from `decimal`) with fixed precision/rounding (e.g., `ROUND_HALF_EVEN`).
- **Structure**
  - Separate presentation (CLI/scanner), business logic (Transaction/PDFEngine), and data access concerns for reuse and testing.
  - Use dependency injection for configuration/paths; apply additional layering only where it adds value.
- **Configuration**
  - Read paths/colors from config or env, and provide a fallback for missing assets (logo).
- **Logging**
  - Replace `print` with `logging` levels so failed scans are visible without user prompts.
- **Tests**
  - Add unit tests for `_parse_amount`, IBAN formatting, and QR payload lines to prevent regressions.
# DocuGen - Document Generation Application

A simple web application with user authentication for document generation.

## Features

- User registration and login
- Secure password hashing using Werkzeug
- Session-based authentication
- **PDF Document Generation** with multiple templates:
  - Professional Letters
  - Invoices
  - Reports
  - General Documents
- Document history and management
- Download and delete documents
- Clean and responsive UI
- SQLite database for user and document management

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
4. **Generate Documents**: Click "Generate Document" to create professional PDFs
   - Choose from Letter, Invoice, Report, or General document types
   - Fill in the title and content
   - Download your formatted PDF instantly
5. **Manage Documents**: View, download, or delete your document history
6. **Logout**: Sign out using the logout button in the navigation

## Security Features

- Password hashing with Werkzeug's `generate_password_hash`
- Session-based authentication
- Login required decorator for protected routes
- Input validation on registration and login forms
- CSRF protection through Flask's session management

## Configuration

The application uses environment variables for configuration:

- `SECRET_KEY`: Secret key for session management (auto-generated if not set, but should be set in production)
- `FLASK_DEBUG`: Set to 'true' to enable debug mode (defaults to false for security)
- `FLASK_HOST`: Host to bind to (defaults to 127.0.0.1)
- `FLASK_PORT`: Port to run on (defaults to 5000)

### Production Deployment

For production deployment, you **must** set these environment variables:

```bash
export SECRET_KEY='your-strong-random-secret-key-here'
export FLASK_DEBUG='false'
export FLASK_HOST='0.0.0.0'  # Only if needed
```

**Important**: Do not run the Flask development server in production. Use a production WSGI server like Gunicorn or uWSGI.

## Database

The application uses SQLite with the following schema:

**Users Table:**
- `id`: Primary key
- `username`: Unique username (3+ characters)
- `email`: Unique email address
- `password_hash`: Hashed password

**Documents Table:**
- `id`: Primary key
- `title`: Document title
- `doc_type`: Document type (letter, invoice, report, general)
- `content`: Document content (text)
- `created_at`: Timestamp of document creation
- `user_id`: Foreign key to Users table

## Development

The application is built with:
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- Werkzeug 3.0.3
- ReportLab 4.0.7 (for PDF generation)
- Python-dateutil 2.8.2

## Future Enhancements

- Advanced PDF templates with custom styling
- Document templates library
- Bulk document generation
- User profile management
- Password reset functionality
- Email verification
- OAuth integration
- Document sharing and collaboration
- Export to multiple formats (Word, HTML)

## License

This project is provided as-is for educational and development purposes.
