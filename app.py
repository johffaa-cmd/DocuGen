"""
DocuGen - Document Generation Application with User Authentication
"""
import os
import secrets
import re
from datetime import datetime
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas

app = Flask(__name__)

# Security: Generate a secure random key if not provided
if 'SECRET_KEY' not in os.environ:
    # In development, generate a random key
    # In production, this should be set as an environment variable
    app.config['SECRET_KEY'] = secrets.token_hex(32)
    print("WARNING: Using auto-generated SECRET_KEY. Set SECRET_KEY environment variable for production!")
else:
    app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///docugen.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

ALLOWED_DOC_TYPES = {'letter', 'invoice', 'report', 'general'}
ALLOWED_AI_FILE_EXTENSIONS = {'txt', 'md'}
MAX_AI_FILE_SIZE = 50 * 1024  # 50KB cap to avoid large uploads
MAX_SUMMARY_LENGTH = 320
MAX_TITLE_LENGTH = 80
TITLE_TRUNCATE_LENGTH = 77
BULLET_STRIP_CHARS = ' -•\t'


class User(db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    documents = db.relationship('Document', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Document(db.Model):
    """Document model for tracking generated documents"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    doc_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Document {self.title}>'


def normalize_doc_type(doc_type):
    """Return a supported document type or default to general."""
    normalized = (doc_type or '').lower()
    return normalized if normalized in ALLOWED_DOC_TYPES else 'general'


def clean_text(value):
    """Strip control characters to keep generated content safe."""
    if not value:
        return ''
    normalized = value.replace('\r\n', '\n').replace('\r', '\n')
    # Remove non-printable/control characters but preserve tabs/newlines
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', normalized)
    return sanitized.strip()


def load_text_from_upload(upload):
    """Extract safe text from an uploaded file."""
    if not upload or not upload.filename:
        return ''

    filename = secure_filename(upload.filename)
    if not filename:
        return ''

    ext = filename.rpartition('.')[2].lower() if '.' in filename else ''
    if not ext or ext not in ALLOWED_AI_FILE_EXTENSIONS:
        raise ValueError('Unsupported file type. Please upload a .txt or .md file.')

    data = upload.read(MAX_AI_FILE_SIZE + 1)
    if len(data) > MAX_AI_FILE_SIZE:
        raise ValueError('File too large. Please upload a file smaller than 50KB.')

    return data.decode('utf-8', errors='replace')


def _summarize_text(text):
    """Generate a short summary from provided text."""
    cleaned = clean_text(text)
    if not cleaned:
        return ''
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    if sentences and sentences[0].strip():
        return ' '.join(sentences[:2]).strip()
    return cleaned[:MAX_SUMMARY_LENGTH].strip()


def generate_ai_draft(prompt_text, file_text, doc_type):
    """
    Generate a deterministic AI-like draft based on prompt and optional file text.
    
    Args:
        prompt_text (str): Freeform user prompt describing desired output.
        file_text (str): Optional supporting context text.
        doc_type (str): Document type key (letter, invoice, report, general).

    Returns:
        tuple[str, str]: Suggested (title, content) strings.
    """
    doc_type = normalize_doc_type(doc_type)
    prompt_text = clean_text(prompt_text)
    file_text = clean_text(file_text)

    combined_parts = [part for part in [prompt_text, file_text] if part]
    combined = '\n'.join(combined_parts)
    if combined_parts:
        summary = _summarize_text(combined) or "Automated content generated from your inputs."
    else:
        summary = "Automated content generated from your inputs."

    # Derive a concise title
    if not prompt_text and not file_text:
        title_candidate = f"AI {doc_type.capitalize()} Draft"
    else:
        title_source = prompt_text or summary
        title_candidate = title_source.splitlines()[0] if title_source else ''
        title_candidate = re.sub(r'\s+', ' ', title_candidate).strip()
        if len(title_candidate) > MAX_TITLE_LENGTH:
            title_candidate = title_candidate[:TITLE_TRUNCATE_LENGTH].rstrip() + '...'
        if not title_candidate:
            title_candidate = f"AI {doc_type.capitalize()} Draft"

    # Collect bullet-style highlights
    raw_lines = []
    for line in combined.splitlines():
        if not line.strip():
            continue
        stripped = line.strip(BULLET_STRIP_CHARS)
        if stripped:
            raw_lines.append(stripped)
    bullet_points = raw_lines[:4]
    if not bullet_points:
        bullet_points = [summary]

    section_templates = {
        'letter': ['Purpose', 'Key Points', 'Closing'],
        'invoice': ['Scope Summary', 'Deliverables', 'Next Steps'],
        'report': ['Context', 'Findings', 'Recommendations'],
        'general': ['Overview', 'Details', 'Actions']
    }
    sections = []
    for idx, heading in enumerate(section_templates[doc_type]):
        section_lines = []
        if idx == 0:
            section_lines.append(summary)
        else:
            for point in bullet_points:
                section_lines.append(f"- {point}")
        sections.append(f"{heading}\n" + '\n'.join(section_lines))

    content = '\n\n'.join(sections)
    return title_candidate, content


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('dashboard.html', user=user)
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if len(username) < 3:
            flash('Username must be at least 3 characters long.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please provide both username and password.', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    username = session.get('username', '')
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    user = User.query.get(session['user_id'])
    documents = Document.query.filter_by(user_id=user.id).order_by(Document.created_at.desc()).all()
    return render_template('dashboard.html', user=user, documents=documents)


@app.route('/generate', methods=['GET', 'POST'])
@login_required
def generate_document():
    """Generate a new document"""
    form_state = {
        'doc_type': '',
        'title': '',
        'content': '',
        'ai_prompt': '',
        'max_ai_size_kb': MAX_AI_FILE_SIZE // 1024
    }
    if request.method == 'POST':
        action = request.form.get('action', 'create')
        doc_type = normalize_doc_type(request.form.get('doc_type', ''))
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        ai_prompt = request.form.get('ai_prompt', '').strip()

        form_state.update({'doc_type': doc_type, 'title': title, 'content': content, 'ai_prompt': ai_prompt})

        if action == 'ai_generate':
            try:
                file_text = load_text_from_upload(request.files.get('ai_file'))
            except ValueError as exc:
                flash(str(exc), 'error')
                return render_template('generate.html', **form_state)

            if not ai_prompt and not file_text:
                flash('Provide a prompt or upload a text/markdown file for AI generation.', 'error')
                return render_template('generate.html', **form_state)

            generated_title, generated_content = generate_ai_draft(ai_prompt, file_text, doc_type)
            form_state['title'] = title or generated_title
            form_state['content'] = generated_content
            flash('AI draft generated. Review and edit before creating the PDF.', 'info')
            return render_template('generate.html', **form_state)

        # Validation for manual or AI-refined submission
        if not doc_type:
            flash('Document type is required.', 'error')
            return render_template('generate.html', **form_state)

        if not title:
            flash('Document title is required.', 'error')
            return render_template('generate.html', **form_state)

        # Create document record
        document = Document(
            title=title,
            doc_type=doc_type,
            content=content,
            user_id=session['user_id']
        )
        db.session.add(document)
        db.session.commit()

        flash(f'Document "{title}" created successfully!', 'success')
        return redirect(url_for('download_document', doc_id=document.id))

    return render_template('generate.html', **form_state)


@app.route('/download/<int:doc_id>')
@login_required
def download_document(doc_id):
    """Download a generated document"""
    document = Document.query.get_or_404(doc_id)
    
    # Verify ownership
    if document.user_id != session['user_id']:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get user once for all PDF generation functions
    user = User.query.get(document.user_id)
    
    # Generate PDF
    pdf_buffer = BytesIO()
    
    if document.doc_type == 'letter':
        generate_letter_pdf(pdf_buffer, document, user)
    elif document.doc_type == 'invoice':
        generate_invoice_pdf(pdf_buffer, document, user)
    elif document.doc_type == 'report':
        generate_report_pdf(pdf_buffer, document, user)
    else:
        generate_simple_pdf(pdf_buffer, document, user)
    
    pdf_buffer.seek(0)
    
    # Sanitize filename to prevent directory traversal and special characters
    safe_title = secure_filename(document.title)
    if not safe_title:  # If title is all special chars, use a default
        safe_title = "document"
    filename = f"{safe_title}_{document.id}.pdf"
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


@app.route('/delete/<int:doc_id>', methods=['POST'])
@login_required
def delete_document(doc_id):
    """Delete a document"""
    document = Document.query.get_or_404(doc_id)
    
    # Verify ownership
    if document.user_id != session['user_id']:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    title = document.title
    db.session.delete(document)
    db.session.commit()
    
    flash(f'Document "{title}" deleted successfully.', 'success')
    return redirect(url_for('dashboard'))


def generate_simple_pdf(buffer, document, user):
    """Generate a simple PDF document"""
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=1  # Center
    )
    story.append(Paragraph(document.title, title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Document info
    info_style = styles['Normal']
    story.append(Paragraph(f"<b>Created by:</b> {user.username}", info_style))
    story.append(Paragraph(f"<b>Date:</b> {document.created_at.strftime('%B %d, %Y')}", info_style))
    story.append(Paragraph(f"<b>Type:</b> {document.doc_type.capitalize()}", info_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Content
    if document.content:
        content_style = styles['BodyText']
        for paragraph in document.content.split('\n'):
            if paragraph.strip():
                story.append(Paragraph(paragraph, content_style))
                story.append(Spacer(1, 0.1 * inch))
    
    doc.build(story)


def generate_letter_pdf(buffer, document, user):
    """Generate a professional letter PDF"""
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Header with date
    date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], alignment=2)  # Right align
    story.append(Paragraph(document.created_at.strftime('%B %d, %Y'), date_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Title
    title_style = ParagraphStyle(
        'LetterTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=20
    )
    story.append(Paragraph(document.title, title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Content
    if document.content:
        body_style = styles['BodyText']
        for paragraph in document.content.split('\n'):
            if paragraph.strip():
                story.append(Paragraph(paragraph, body_style))
                story.append(Spacer(1, 0.15 * inch))
    
    # Signature
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(f"Sincerely,", styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"<b>{user.username}</b>", styles['Normal']))
    
    doc.build(story)


def generate_invoice_pdf(buffer, document, user):
    """Generate an invoice PDF"""
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Header
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#667eea'),
        alignment=1
    )
    story.append(Paragraph("INVOICE", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Invoice details
    invoice_data = [
        ['Invoice Title:', document.title],
        ['Invoice Date:', document.created_at.strftime('%B %d, %Y')],
        ['From:', user.username],
        ['Email:', user.email]
    ]
    
    invoice_table = Table(invoice_data, colWidths=[2 * inch, 4 * inch])
    invoice_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#667eea')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(invoice_table)
    story.append(Spacer(1, 0.4 * inch))
    
    # Content/Description
    if document.content:
        story.append(Paragraph("<b>Description:</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))
        body_style = styles['BodyText']
        for paragraph in document.content.split('\n'):
            if paragraph.strip():
                story.append(Paragraph(paragraph, body_style))
                story.append(Spacer(1, 0.1 * inch))
    
    doc.build(story)


def generate_report_pdf(buffer, document, user):
    """Generate a professional report PDF"""
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Cover page
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=32,
        textColor=colors.HexColor('#667eea'),
        alignment=1,
        spaceAfter=30
    )
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph(document.title, title_style))
    story.append(Spacer(1, 0.5 * inch))
    
    # Report metadata
    meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], alignment=1, fontSize=12)
    story.append(Paragraph(f"Prepared by: {user.username}", meta_style))
    story.append(Paragraph(f"Date: {document.created_at.strftime('%B %d, %Y')}", meta_style))
    story.append(Spacer(1, 1 * inch))
    
    # Content section
    if document.content:
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=15,
            spaceBefore=20
        )
        story.append(Paragraph("Executive Summary", section_style))
        
        body_style = styles['BodyText']
        for paragraph in document.content.split('\n'):
            if paragraph.strip():
                story.append(Paragraph(paragraph, body_style))
                story.append(Spacer(1, 0.15 * inch))
    
    doc.build(story)


def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print('Database initialized successfully.')


if __name__ == '__main__':
    init_db()
    # Get debug mode from environment, default to False for safety
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    # In production, host should be configured by WSGI server
    # For development, allow override via environment variable
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', '5000'))
    
    if debug_mode:
        print("WARNING: Running in debug mode. This should only be used in development!")
    
    app.run(debug=debug_mode, host=host, port=port)
