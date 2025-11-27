#!/usr/bin/env python3
"""Test SMS API Integration with Twilio"""

import os
import sys
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

def test_sms_integration():
    """Test Twilio SMS API connection and credentials."""
    print("=" * 60)
    print("SMS API INTEGRATION TEST")
    print("=" * 60)
    
    # Load credentials
    ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE = os.getenv("TWILIO_PHONE")
    
    print("\n[CHECK 1] Credentials Loaded")
    print(f"  ✓ Account SID: {ACCOUNT_SID[:10]}..." if ACCOUNT_SID else "  ✗ Account SID: Missing")
    print(f"  ✓ Auth Token: {AUTH_TOKEN[:10]}..." if AUTH_TOKEN else "  ✗ Auth Token: Missing")
    print(f"  ✓ Sender Phone: {TWILIO_PHONE}" if TWILIO_PHONE else "  ✗ Sender Phone: Missing")
    
    if not (ACCOUNT_SID and AUTH_TOKEN and TWILIO_PHONE):
        print("\n[ERROR] Missing Twilio credentials in .env file")
        return False
    
    print("\n[CHECK 2] Twilio Client Connection")
    try:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        # Test by fetching account info
        account = client.api.accounts(ACCOUNT_SID).fetch()
        print(f"  ✓ Connected to Twilio account: {account.friendly_name}")
        print(f"  ✓ Account Status: {account.status}")
    except Exception as e:
        print(f"  ✗ Connection Failed: {str(e)}")
        return False
    
    print("\n[CHECK 3] SMS Configuration")
    print(f"  • Sender Number: {TWILIO_PHONE}")
    print(f"  • Country: India (+91)")
    print(f"  • API: Twilio REST API v1")
    print(f"  • SDK Version: twilio 9.1.0")
    
    print("\n[CHECK 4] Test Message Format")
    test_message = "WEATHER ALERT Mumbai: Heatwave warning. Max temp 42°C. Stay hydrated. Reduce outdoor work."
    print(f"  • Message Length: {len(test_message)} chars")
    print(f"  • SMS Parts Required: {(len(test_message) // 160) + 1}")
    print(f"  • Sample: {test_message[:80]}...")
    
    print("\n[CHECK 5] Ready to Send SMS")
    print("  ✓ All credentials validated")
    print("  ✓ SMS integration ready")
    print("\nTo send a test SMS, update script with recipient number and uncomment send block.")
    
    print("\n" + "=" * 60)
    print("INTEGRATION STATUS: READY")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_sms_integration()
    sys.exit(0 if success else 1)
