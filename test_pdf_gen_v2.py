"""
Tests for PDF Generation Module (v2)
Verifies that high-fidelity templates are generated without errors.
"""
import os
import unittest
from io import BytesIO
from datetime import datetime
from pdf_generator import dispatch_pdf_generation

class MockUser:
    username = "test_user"
    email = "test@example.com"

class MockDocument:
    def __init__(self, doc_type, title, content):
        self.id = 12345
        self.doc_type = doc_type
        self.title = title
        self.content = content
        self.created_at = datetime.utcnow()

class TestPDFGenerator(unittest.TestCase):

    def test_generate_receipt(self):
        print("\nTesting Receipt Generation...")
        doc = MockDocument(
            'receipt', 
            'Apple Store Purchase', 
            "MacBook Pro: 2500.00\nMagic Mouse: 99.00"
        )
        user = MockUser()
        buffer = BytesIO()
        
        try:
            dispatch_pdf_generation(buffer, doc, user)
            pdf_content = buffer.getvalue()
            self.assertTrue(len(pdf_content) > 1000, "PDF should be substantial size")
            self.assertTrue(pdf_content.startswith(b'%PDF'), "Output must be a PDF")
            print("[PASS] Receipt generated successfully.")
        except Exception as e:
            self.fail(f"Receipt generation failed: {e}")

    def test_generate_high_fidelity_look(self):
        # We can't visual check but we can check if it runs for other types too
        types = ['invoice', 'report', 'letter', 'general']
        for t in types:
            print(f"Testing {t.capitalize()} Generation...")
            doc = MockDocument(t, f"Test {t}", "Sample content line 1.\nSample content line 2.")
            user = MockUser()
            buffer = BytesIO()
            dispatch_pdf_generation(buffer, doc, user)
            self.assertTrue(len(buffer.getvalue()) > 0)
            print(f"[PASS] {t.capitalize()} generated.")

if __name__ == '__main__':
    unittest.main()
