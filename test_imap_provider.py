"""
Test script for the IMAP/SMTP provider.
"""

import os
import asyncio
import getpass
import json
from typing import Dict, Any

from ergon.core.agents.mail.imap_provider import ImapSmtpProvider


async def test_imap_provider():
    """Test the IMAP/SMTP provider with Gmail."""
    print("\n=== Testing IMAP/SMTP Provider ===\n")
    
    # Get credentials
    email = input("Enter email address: ")
    password = getpass.getpass("Enter password or app password: ")
    
    # Determine server settings based on email domain
    domain = email.split('@')[-1]
    if domain == 'gmail.com':
        imap_server = 'imap.gmail.com'
        smtp_server = 'smtp.gmail.com'
        print(f"\nUsing Gmail servers: {imap_server}, {smtp_server}")
    elif domain in ('outlook.com', 'hotmail.com', 'live.com'):
        imap_server = 'outlook.office365.com'
        smtp_server = 'smtp.office365.com'
        print(f"\nUsing Outlook servers: {imap_server}, {smtp_server}")
    else:
        imap_server = input(f"Enter IMAP server for {domain}: ")
        smtp_server = input(f"Enter SMTP server for {domain} (or press Enter to use same as IMAP): ") or imap_server
    
    # Log configuration (with redacted password)
    print(f"\nProvider configuration:")
    print(f"- Email: {email}")
    print(f"- Password: **REDACTED**")
    print(f"- IMAP Server: {imap_server}")
    print(f"- SMTP Server: {smtp_server}")
    
    # Create provider
    provider = ImapSmtpProvider(
        email_address=email,
        password=password,
        imap_server=imap_server,
        smtp_server=smtp_server,
        imap_port=993,
        smtp_port=587,
        use_ssl=True,
        smtp_use_tls=True
    )
    
    # Test authentication
    print("\nAuthenticating...", end="", flush=True)
    auth_result = await provider.authenticate()
    if auth_result:
        print(" ✓ Success!")
    else:
        print(" ✗ Failed!")
        return False
    
    # Test inbox retrieval
    print("\nRetrieving inbox...", end="", flush=True)
    inbox = await provider.get_inbox(limit=5)
    if inbox:
        print(f" ✓ Success! Found {len(inbox)} messages.")
        print("\nRecent messages:")
        for i, msg in enumerate(inbox[:3], 1):
            print(f"  {i}. {msg['subject']} (From: {msg['from']})")
    else:
        print(" ✓ Success! (No messages found or empty inbox)")
    
    # Test folder listing
    print("\nRetrieving folders...", end="", flush=True)
    folders = await provider.get_folders()
    if folders:
        print(f" ✓ Success! Found {len(folders)} folders.")
        print("\nFolders:")
        for i, folder in enumerate(folders[:5], 1):
            print(f"  {i}. {folder['name']} ({folder['total_items']} items, {folder['unread_items']} unread)")
    else:
        print(" ✗ Failed! No folders found.")
    
    # Ask if user wants to send a test email
    send_test = input("\nDo you want to send a test email? (y/n): ").lower() == 'y'
    if send_test:
        to_email = input("Enter recipient email: ")
        
        # Send test email
        print("\nSending test email...", end="", flush=True)
        result = await provider.send_message(
            to=[to_email],
            subject="Ergon IMAP/SMTP Test",
            body="This is a test email from Ergon IMAP/SMTP provider."
        )
        
        if result:
            print(" ✓ Success!")
        else:
            print(" ✗ Failed!")
    
    print("\nTests completed!")
    return True


if __name__ == "__main__":
    asyncio.run(test_imap_provider())