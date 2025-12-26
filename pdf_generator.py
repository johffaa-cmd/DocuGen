import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# --- Bank Profile Configurations ---
class BankProfile:
    def __init__(self, key, name, color_primary, color_secondary, logo_path=None):
        self.key = key
        self.name = name
        self.color_primary = colors.HexColor(color_primary)
        self.color_secondary = colors.HexColor(color_secondary)
        self.logo_path = logo_path

BANK_PROFILES = {
    'ing': BankProfile('ing', 'ING Bank', '#FF6200', '#333333'), # Orange / Dark Grey
    'abn': BankProfile('abn', 'ABN AMRO', '#009286', '#FDB000'), # Teal / Yellow
    'rabo': BankProfile('rabo', 'Rabobank', '#FF4E00', '#000099'), # Orange / Blue
    'generic': BankProfile('generic', 'Bank Payment', '#2c3e50', '#95a5a6')
}

def get_logo(profile_key):
    """Try to find a local logo file, else return None"""
    # Assuming logos are stored in static/logos/
    path = os.path.join(os.getcwd(), 'static', 'logos', f'{profile_key}.png')
    if os.path.exists(path):
        return path
    return None

def draw_header_footer(canvas, doc, profile):
    """Draws fixed header/footer elements based on bank profile"""
    canvas.saveState()
    
    # --- ING STYLE ---
    if profile.key == 'ing':
        # Top Orange Bar
        canvas.setFillColor(profile.color_primary)
        canvas.rect(0, A4[1] - 20*mm, A4[0], 20*mm, fill=1, stroke=0)
        # Logo placeholder text if no image
        if not profile.logo_path:
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 24)
            canvas.drawString(20*mm, A4[1] - 13*mm, "ING")
        else:
            # Draw logo image
            pass 

        # Footer
        canvas.setFillColor(colors.black)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(20*mm, 15*mm, f"ING Bank N.V. is ingeschreven bij de KvK onder nummer 33031431.")

    # --- ABN STYLE ---
    elif profile.key == 'abn':
        # Green header block
        canvas.setFillColor(profile.color_primary)
        canvas.rect(0, A4[1] - 30*mm, A4[0], 30*mm, fill=1, stroke=0)
        # Yellow accent line
        canvas.setStrokeColor(profile.color_secondary)
        canvas.setLineWidth(2)
        canvas.line(20*mm, A4[1] - 32*mm, A4[0]-20*mm, A4[1] - 32*mm)
        
        if not profile.logo_path:
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 20)
            canvas.drawString(25*mm, A4[1] - 20*mm, "ABN AMRO")

    # --- RABO STYLE ---
    elif profile.key == 'rabo':
        # Very clean, usually logo top left
        canvas.setFillColor(profile.color_primary)
        # Vertical accent on the right?
        # Let's do a simple logo text for now
        canvas.setFillColor(profile.color_secondary)
        canvas.setFont("Helvetica-Bold", 22)
        canvas.drawString(20*mm, A4[1] - 25*mm, "Rabobank")
        
        # Orange bottom bar
        canvas.setFillColor(profile.color_primary)
        canvas.rect(0, 0, A4[0], 5*mm, fill=1, stroke=0)

    canvas.restoreState()


def generate_bank_receipt(buffer, document, user, bank_key='generic'):
    """
    Generate a high-fidelity bank transaction receipt.
    Recreates the layout of a payment confirmation.
    """
    profile = BANK_PROFILES.get(bank_key, BANK_PROFILES['generic'])
    profile.logo_path = get_logo(bank_key)

    # Custom Document Template to allow background drawing (headers/footers)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=40*mm,
        bottomMargin=30*mm
    )

    # Define a Frame and PageTemplate to attach the header drawer
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    
    def on_page(c, d):
        draw_header_footer(c, d, profile)

    template = PageTemplate(id='bank_template', frames=[frame], onPage=on_page)
    doc.addPageTemplates([template])

    story = []
    styles = getSampleStyleSheet()
    
    # --- Parsing Content ---
    # Expecting key: value pairs in content
    data = {}
    lines = document.content.split('\n')
    for line in lines:
        if ':' in line:
            k, v = line.split(':', 1)
            data[k.strip().lower()] = v.strip()
            
    # Defaults/Fallbacks
    amount = data.get('bedrag', data.get('amount', '€ 0,00'))
    if '€' not in amount and '$' not in amount: amount = f"€ {amount}"
    
    iban_from = data.get('van rekening', data.get('from', 'NL00 BANK 0000 0000 00'))
    name_from = data.get('naam', data.get('from_name', user.username))
    
    iban_to = data.get('naar rekening', data.get('to', 'NL00 BANK 0000 0000 00'))
    name_to = data.get('ontvanger', data.get('to_name', 'Unknown Recipient'))
    
    date_str = document.created_at.strftime('%d-%m-%Y')
    desc = data.get('omschrijving', data.get('description', document.title))

    # --- Main Content Construction ---

    # 1. Title
    title_style = ParagraphStyle(
        'BankTitle', 
        parent=styles['Heading1'], 
        fontSize=18, 
        textColor=profile.color_secondary if profile.key == 'rabo' else colors.black
    )
    story.append(Paragraph("Betaalbewijs", title_style))
    story.append(Spacer(1, 10*mm))

    # 2. Amount Big
    amount_style = ParagraphStyle(
        'Amount',
        parent=styles['Normal'],
        fontSize=24,
        fontName='Helvetica-Bold',
        textColor=colors.black
    )
    story.append(Paragraph(amount, amount_style))
    story.append(Paragraph(f"Afgeschreven op {date_str}", styles['Normal']))
    story.append(Spacer(1, 10*mm))
    
    # 3. Details Table
    # A generic "Key - Value" table style that looks clean
    
    rows = [
        ['Naam', name_from],
        ['Van rekening', iban_from],
        ['', ''], # Spacer
        ['Naam ontvanger', name_to],
        ['Naar rekening', iban_to],
        ['', ''],
        ['Omschrijving', desc],
        ['Datum', date_str],
        ['Transactie type', 'Overschrijving']
    ]

    tbl = Table(rows, colWidths=[50*mm, 100*mm])
    
    # Specific Table Styles per Bank
    common_style = [
        ('FONTNAME', (0,0), (0,-1), 'Helvetica'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (0,-1), colors.gray),
        ('TEXTCOLOR', (1,0), (1,-1), colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]
    
    if profile.key == 'ing':
        # ING often uses subtle lines
        common_style.append(('LINEBELOW', (0,0), (1,-1), 0.5, colors.lightgrey))
        
    elif profile.key == 'abn':
        # ABN clean, maybe no lines inside, just spacing
        pass
        
    tbl.setStyle(TableStyle(common_style))
    
    story.append(tbl)
    story.append(Spacer(1, 15*mm))
    
    # 4. Verification/Footer Note
    note_style = ParagraphStyle('Note', parent=styles['Normal'], fontSize=8, textColor=colors.gray)
    story.append(Paragraph("Dit betaalbewijs is gegenereerd door DocuGen en dient ter bevestiging van de transactiegegevens.", note_style))
    
    doc.build(story)


# --- Dispatcher Update ---
def dispatch_pdf_generation(buffer, document, user, bank_style='generic'):
    """Route to appropriate generator"""
    if document.doc_type == 'receipt':
        # "receipt" now implies bank receipt if a style is provided
        generate_bank_receipt(buffer, document, user, bank_style)
    # ... fallback to others for legacy types (invoice, letter etc)
    # (For brevity in this update, I'm focusing on the requested functionality)
    elif document.doc_type == 'invoice':
        from pdf_generator_legacy import generate_invoice_pdf # We might need to keep old funcs
        generate_invoice_pdf(buffer, document, user)
    else:
        # Default simple
        from pdf_generator_legacy import generate_general_pdf
        generate_general_pdf(buffer, document, user)

# Quick fix: include the legacy functions here so it doesn't break
def generate_invoice_pdf(buffer, document, user):
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    doc = SimpleDocTemplate(buffer)
    story = [Paragraph(f"Invoice: {document.title}", getSampleStyleSheet()['Normal'])]
    doc.build(story)

def generate_general_pdf(buffer, document, user):
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    doc = SimpleDocTemplate(buffer)
    story = [Paragraph(document.content or "Content", getSampleStyleSheet()['Normal'])]
    doc.build(story)
