"""
Test script for DocuGen user authentication
"""
import os
import sys
from app import app, db, User

def test_user_operations():
    """Test user registration and authentication"""
    print("Testing DocuGen User Authentication System\n")
    print("=" * 50)
    
    # Test within app context
    with app.app_context():
        # Initialize database
        print("\n1. Initializing database...")
        db.create_all()
        print("   ✓ Database initialized")
        
        # Test user creation
        print("\n2. Testing user creation...")
        test_user = User(username='testuser', email='test@example.com')
        test_user.set_password('password123')
        
        db.session.add(test_user)
        db.session.commit()
        print(f"   ✓ User created: {test_user.username}")
        
        # Test user retrieval
        print("\n3. Testing user retrieval...")
        retrieved_user = User.query.filter_by(username='testuser').first()
        assert retrieved_user is not None, "User not found"
        print(f"   ✓ User retrieved: {retrieved_user.username} (ID: {retrieved_user.id})")
        
        # Test password verification
        print("\n4. Testing password verification...")
        assert retrieved_user.check_password('password123'), "Password check failed"
        print("   ✓ Correct password verified")
        
        assert not retrieved_user.check_password('wrongpassword'), "Wrong password accepted"
        print("   ✓ Wrong password rejected")
        
        # Test unique constraints
        print("\n5. Testing unique constraints...")
        duplicate_user = User(username='testuser', email='another@example.com')
        duplicate_user.set_password('password123')
        db.session.add(duplicate_user)
        
        try:
            db.session.commit()
            print("   ✗ Duplicate username was allowed (should have failed)")
            sys.exit(1)
        except Exception as e:
            db.session.rollback()
            print("   ✓ Duplicate username rejected")
        
        # Clean up
        print("\n6. Cleaning up test data...")
        User.query.delete()
        db.session.commit()
        print("   ✓ Test data cleaned up")
        
        print("\n" + "=" * 50)
        print("All tests passed! ✓")
        print("=" * 50)

if __name__ == '__main__':
    # Remove existing test database if it exists
    if os.path.exists('docugen.db'):
        os.remove('docugen.db')
    
    test_user_operations()
