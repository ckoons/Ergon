"""
Mail Provider Adapters for Agenteer Mail Agent.

This module defines the interfaces and implementations for different
email service providers (Gmail, Outlook, etc.)
"""

import os
import json
import base64
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import urllib.parse
import secrets
import webbrowser
import time

import httpx
# Gmail imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
# Outlook imports
from msal import PublicClientApplication, SerializableTokenCache

from agenteer.utils.config.settings import settings

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.log_level.value))


class MailProvider(ABC):
    """Base interface for mail providers."""
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the provider."""
        pass
    
    @abstractmethod
    async def get_inbox(self, limit: int = 20, page: int = 1) -> List[Dict[str, Any]]:
        """Retrieve inbox messages."""
        pass
    
    @abstractmethod
    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """Retrieve a specific message by ID."""
        pass
    
    @abstractmethod
    async def send_message(self, to: List[str], subject: str, body: str, 
                           cc: Optional[List[str]] = None,
                           bcc: Optional[List[str]] = None) -> bool:
        """Send a new message."""
        pass
    
    @abstractmethod
    async def reply_to_message(self, message_id: str, body: str) -> bool:
        """Reply to a specific message."""
        pass
    
    @abstractmethod
    async def search_messages(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for messages using provider-specific query."""
        pass
    
    @abstractmethod
    async def get_folders(self) -> List[Dict[str, Any]]:
        """Get available folders/labels."""
        pass


class GmailProvider(MailProvider):
    """Gmail implementation of MailProvider."""
    
    # Gmail API scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
              'https://www.googleapis.com/auth/gmail.send',
              'https://www.googleapis.com/auth/gmail.labels']
    
    def __init__(self, credentials_file: Optional[str] = None, token_file: Optional[str] = None):
        """
        Initialize Gmail provider.
        
        Args:
            credentials_file: Path to OAuth client credentials
            token_file: Path to store/retrieve OAuth tokens
        """
        self.credentials_file = credentials_file or os.path.join(
            settings.config_path, "gmail_credentials.json")
        self.token_file = token_file or os.path.join(
            settings.config_path, "gmail_token.json")
        self.credentials = None
        self.email = None
        self.api_base = "https://gmail.googleapis.com/gmail/v1"
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Gmail API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Check if we already have a token
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as token:
                    creds_data = json.load(token)
                    self.credentials = Credentials.from_authorized_user_info(
                        creds_data, self.SCOPES)
                    
                    # If credentials expired, try to refresh
                    if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                        self.credentials.refresh(Request())
                        # Save refreshed credentials
                        with open(self.token_file, 'w') as token:
                            token.write(self.credentials.to_json())
            
            # If no valid credentials, need to authenticate
            if not self.credentials or not self.credentials.valid:
                if not os.path.exists(self.credentials_file):
                    logger.error(f"Gmail credentials file not found: {self.credentials_file}")
                    return False
                
                # Start OAuth flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                self.credentials = flow.run_local_server(port=0)
                
                # Save credentials
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
            
            # Get user email address
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.credentials.token}"
                }
                response = await client.get(
                    f"{self.api_base}/users/me/profile",
                    headers=headers
                )
                
                if response.status_code == 200:
                    self.email = response.json().get("emailAddress")
                    logger.info(f"Authenticated as {self.email}")
                    return True
                else:
                    logger.error(f"Failed to get user profile: {response.text}")
                    return False
                
        except Exception as e:
            logger.error(f"Gmail authentication error: {str(e)}")
            return False
    
    async def get_inbox(self, limit: int = 20, page: int = 1) -> List[Dict[str, Any]]:
        """
        Get inbox messages.
        
        Args:
            limit: Maximum number of messages
            page: Page number (1-based)
            
        Returns:
            List of message metadata
        """
        if not self.credentials or not self.credentials.valid:
            if not await self.authenticate():
                return []
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.credentials.token}"
                }
                
                # Calculate pagination
                max_results = min(limit, 100)  # Gmail API max is 100
                page_token = None
                
                # Get message IDs first
                query = {
                    "maxResults": max_results,
                    "labelIds": "INBOX"
                }
                
                # Add page token if we have one and not on first page
                if page > 1 and page_token:
                    query["pageToken"] = page_token
                
                response = await client.get(
                    f"{self.api_base}/users/me/messages",
                    headers=headers,
                    params=query
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get inbox: {response.text}")
                    return []
                
                response_data = response.json()
                message_ids = [msg["id"] for msg in response_data.get("messages", [])]
                
                # If no messages
                if not message_ids:
                    return []
                
                # Get message details (batch request would be better for production)
                messages = []
                for msg_id in message_ids:
                    message = await self.get_message(msg_id)
                    if message:
                        messages.append(message)
                
                return messages
                
        except Exception as e:
            logger.error(f"Error getting inbox: {str(e)}")
            return []
    
    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """
        Get a specific message by ID.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Message data with headers and body
        """
        if not self.credentials or not self.credentials.valid:
            if not await self.authenticate():
                return {}
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.credentials.token}"
                }
                
                response = await client.get(
                    f"{self.api_base}/users/me/messages/{message_id}",
                    headers=headers,
                    params={"format": "full"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get message {message_id}: {response.text}")
                    return {}
                
                raw_message = response.json()
                
                # Extract headers
                headers_dict = {}
                for header in raw_message["payload"].get("headers", []):
                    headers_dict[header["name"].lower()] = header["value"]
                
                # Extract body
                body = self._extract_body(raw_message["payload"])
                
                # Format message
                message = {
                    "id": message_id,
                    "thread_id": raw_message.get("threadId", ""),
                    "subject": headers_dict.get("subject", "(No subject)"),
                    "from": headers_dict.get("from", ""),
                    "to": headers_dict.get("to", ""),
                    "date": headers_dict.get("date", ""),
                    "body": body,
                    "snippet": raw_message.get("snippet", ""),
                    "labels": raw_message.get("labelIds", [])
                }
                
                return message
                
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {str(e)}")
            return {}
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract body text from message payload."""
        # Check if this part has a body
        if "body" in payload and "data" in payload["body"]:
            data = payload["body"]["data"]
            decoded_data = base64.urlsafe_b64decode(data).decode("utf-8")
            return decoded_data
        
        # If this is multipart, check parts
        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                # Prefer HTML content
                if mime_type == "text/html":
                    if "body" in part and "data" in part["body"]:
                        data = part["body"]["data"]
                        return base64.urlsafe_b64decode(data).decode("utf-8")
                
                # Fall back to text/plain
                if mime_type == "text/plain":
                    if "body" in part and "data" in part["body"]:
                        data = part["body"]["data"]
                        return base64.urlsafe_b64decode(data).decode("utf-8")
                
                # Recursively check nested parts
                if "parts" in part:
                    body = self._extract_body(part)
                    if body:
                        return body
        
        return "(No body content)"
    
    async def send_message(self, to: List[str], subject: str, body: str, 
                           content_type: str = "text/plain",
                           cc: Optional[List[str]] = None,
                           bcc: Optional[List[str]] = None) -> bool:
        """
        Send a new email message.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body (text)
            content_type: Content type of body (text/plain or text/html)
            cc: List of CC recipients
            bcc: List of BCC recipients
            
        Returns:
            True if successful, False otherwise
        """
        if not self.credentials or not self.credentials.valid:
            if not await self.authenticate():
                return False
        
        try:
            # Build email message
            message = f"From: {self.email}\r\n"
            message += f"To: {', '.join(to)}\r\n"
            
            if cc:
                message += f"Cc: {', '.join(cc)}\r\n"
            
            message += f"Subject: {subject}\r\n"
            message += f"Content-Type: {content_type}; charset=utf-8\r\n\r\n"
            message += body
            
            # Encode as base64url
            encoded_message = base64.urlsafe_b64encode(message.encode("utf-8")).decode("utf-8")
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.credentials.token}",
                    "Content-Type": "application/json"
                }
                
                body_data = {
                    "raw": encoded_message
                }
                
                response = await client.post(
                    f"{self.api_base}/users/me/messages/send",
                    headers=headers,
                    json=body_data
                )
                
                if response.status_code == 200:
                    logger.info(f"Message sent successfully")
                    return True
                else:
                    logger.error(f"Failed to send message: {response.text}")
                    return False
                
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    async def reply_to_message(self, message_id: str, body: str, content_type: str = "text/plain") -> bool:
        """
        Reply to a specific message.
        
        Args:
            message_id: Gmail message ID
            body: Reply body text
            content_type: Content type of body (text/plain or text/html)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.credentials or not self.credentials.valid:
            if not await self.authenticate():
                return False
        
        try:
            # Get original message to extract headers
            original = await self.get_message(message_id)
            if not original:
                logger.error(f"Could not find original message {message_id}")
                return False
            
            # Extract thread ID and recipients
            thread_id = original.get("thread_id", "")
            to_address = self._extract_reply_address(original.get("from", ""))
            subject = original.get("subject", "")
            
            if not subject.startswith("Re:"):
                subject = f"Re: {subject}"
            
            # Build reply message
            message = f"From: {self.email}\r\n"
            message += f"To: {to_address}\r\n"
            message += f"Subject: {subject}\r\n"
            message += f"In-Reply-To: {message_id}\r\n"
            message += f"References: {message_id}\r\n"
            message += f"Content-Type: {content_type}; charset=utf-8\r\n\r\n"
            message += body
            
            # Encode as base64url
            encoded_message = base64.urlsafe_b64encode(message.encode("utf-8")).decode("utf-8")
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.credentials.token}",
                    "Content-Type": "application/json"
                }
                
                body_data = {
                    "raw": encoded_message,
                    "threadId": thread_id
                }
                
                response = await client.post(
                    f"{self.api_base}/users/me/messages/send",
                    headers=headers,
                    json=body_data
                )
                
                if response.status_code == 200:
                    logger.info(f"Reply sent successfully")
                    return True
                else:
                    logger.error(f"Failed to send reply: {response.text}")
                    return False
                
        except Exception as e:
            logger.error(f"Error sending reply: {str(e)}")
            return False
    
    def _extract_reply_address(self, from_header: str) -> str:
        """Extract email address from From header."""
        # Simple extraction, would need more robust parsing in production
        if "<" in from_header and ">" in from_header:
            # Format: "Name <email@example.com>"
            start = from_header.find("<") + 1
            end = from_header.find(">")
            return from_header[start:end]
        return from_header
    
    async def search_messages(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for messages using Gmail query syntax.
        
        Args:
            query: Gmail search query string
            limit: Maximum number of results
            
        Returns:
            List of matching messages
        """
        if not self.credentials or not self.credentials.valid:
            if not await self.authenticate():
                return []
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.credentials.token}"
                }
                
                # Get message IDs matching query
                params = {
                    "q": query,
                    "maxResults": min(limit, 100)  # Gmail API max is 100
                }
                
                response = await client.get(
                    f"{self.api_base}/users/me/messages",
                    headers=headers,
                    params=params
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to search messages: {response.text}")
                    return []
                
                response_data = response.json()
                message_ids = [msg["id"] for msg in response_data.get("messages", [])]
                
                # If no messages match
                if not message_ids:
                    return []
                
                # Get message details
                messages = []
                for msg_id in message_ids:
                    message = await self.get_message(msg_id)
                    if message:
                        messages.append(message)
                
                return messages
                
        except Exception as e:
            logger.error(f"Error searching messages: {str(e)}")
            return []
    
    async def get_folders(self) -> List[Dict[str, Any]]:
        """
        Get available Gmail labels.
        
        Returns:
            List of label metadata
        """
        if not self.credentials or not self.credentials.valid:
            if not await self.authenticate():
                return []
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.credentials.token}"
                }
                
                response = await client.get(
                    f"{self.api_base}/users/me/labels",
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get labels: {response.text}")
                    return []
                
                response_data = response.json()
                labels = []
                
                for label in response_data.get("labels", []):
                    labels.append({
                        "id": label["id"],
                        "name": label["name"],
                        "type": label["type"]
                    })
                
                return labels
                
        except Exception as e:
            logger.error(f"Error getting labels: {str(e)}")
            return []


class OutlookProvider(MailProvider):
    """Microsoft Outlook/Microsoft 365 implementation of MailProvider."""
    
    # Microsoft Graph API scopes for mail
    SCOPES = [
        "offline_access",  # For refresh tokens
        "User.Read",       # Basic profile info
        "Mail.Read",       # Read mail
        "Mail.Send",       # Send mail
        "Mail.ReadWrite"   # Manage mail
    ]
    
    # Microsoft Graph API endpoints
    GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
    AUTHORITY = "https://login.microsoftonline.com/common"
    
    def __init__(self, 
                 client_id: Optional[str] = None, 
                 token_file: Optional[str] = None,
                 redirect_uri: str = "http://localhost:8000/auth/outlook/callback"):
        """
        Initialize Outlook provider.
        
        Args:
            client_id: Microsoft application client ID
            token_file: Path to store/retrieve tokens
            redirect_uri: OAuth redirect URI
        """
        self.client_id = client_id or settings.outlook_client_id
        self.token_file = token_file or os.path.join(
            settings.config_path, "outlook_token.json")
        self.redirect_uri = redirect_uri
        self.app = None
        self.token_cache = SerializableTokenCache()
        self.access_token = None
        self.email = None
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        
        # Load token cache if exists
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    self.token_cache.deserialize(f.read())
            except Exception as e:
                logger.error(f"Error loading token cache: {str(e)}")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Microsoft Graph API using OAuth.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Initialize the MSAL app
            self.app = PublicClientApplication(
                client_id=self.client_id,
                authority=self.AUTHORITY,
                token_cache=self.token_cache
            )
            
            # Check if we already have accounts in the cache
            accounts = self.app.get_accounts()
            
            if accounts:
                # Use the first account to acquire a token silently
                result = self.app.acquire_token_silent(
                    scopes=self.SCOPES,
                    account=accounts[0]
                )
            else:
                # No accounts in cache, need interactive login
                result = await self._interactive_login()
            
            # Check if we have a valid token
            if result and "access_token" in result:
                self.access_token = result["access_token"]
                
                # Save the token cache
                with open(self.token_file, 'w') as f:
                    f.write(self.token_cache.serialize())
                
                # Get user email address
                await self._get_user_profile()
                
                return True
            else:
                logger.error("Failed to obtain access token")
                return False
                
        except Exception as e:
            logger.error(f"Outlook authentication error: {str(e)}")
            return False
    
    async def _interactive_login(self) -> Dict[str, Any]:
        """
        Perform interactive login using the device code flow.
        
        Returns:
            Authentication result
        """
        # Generate a random state for CSRF protection
        state = secrets.token_urlsafe(16)
        
        # Get the authorization URL
        auth_url = self.app.get_authorization_request_url(
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri,
            state=state
        )
        
        # Open the authorization URL in the browser
        print(f"Please authorize the application in your browser...")
        webbrowser.open(auth_url)
        
        # Create a simple local HTTP server to handle the authorization response
        auth_code = None
        auth_state = None
        
        # Set up a mock server to handle redirect
        # In a real implementation, we would need a proper local server
        # For demonstration, use a simpler approach with manual code input
        print("\nAfter authentication, copy the authorization code from the URL.")
        print("Look for 'code=' parameter in the redirected URL.")
        auth_code = input("Enter the authorization code: ")
        
        # Acquire token with the authorization code
        result = self.app.acquire_token_by_authorization_code(
            code=auth_code,
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )
        
        return result
    
    async def _get_user_profile(self) -> None:
        """Get the user's profile information."""
        if not self.access_token:
            return
        
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = await client.get(
                f"{self.GRAPH_API_ENDPOINT}/me",
                headers=headers
            )
            
            if response.status_code == 200:
                profile = response.json()
                self.email = profile.get("mail") or profile.get("userPrincipalName")
                logger.info(f"Authenticated as {self.email}")
            else:
                logger.error(f"Failed to get user profile: {response.text}")
    
    async def get_inbox(self, limit: int = 20, page: int = 1) -> List[Dict[str, Any]]:
        """
        Get inbox messages.
        
        Args:
            limit: Maximum number of messages
            page: Page number (1-based)
            
        Returns:
            List of message metadata
        """
        if not self.access_token:
            if not await self.authenticate():
                return []
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Calculate skip for pagination
                skip = (page - 1) * limit
                
                # Get messages from inbox
                response = await client.get(
                    f"{self.GRAPH_API_ENDPOINT}/me/mailFolders/inbox/messages",
                    headers=headers,
                    params={
                        "$top": limit,
                        "$skip": skip,
                        "$orderby": "receivedDateTime desc",
                        "$select": "id,subject,from,toRecipients,receivedDateTime,bodyPreview"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get inbox: {response.text}")
                    return []
                
                data = response.json()
                messages = []
                
                for msg_data in data.get("value", []):
                    # Format the message data
                    messages.append({
                        "id": msg_data.get("id", ""),
                        "subject": msg_data.get("subject", "(No subject)"),
                        "from": msg_data.get("from", {}).get("emailAddress", {}).get("address", ""),
                        "to": ", ".join([r.get("emailAddress", {}).get("address", "") 
                                         for r in msg_data.get("toRecipients", [])]),
                        "date": msg_data.get("receivedDateTime", ""),
                        "snippet": msg_data.get("bodyPreview", ""),
                        "has_attachments": msg_data.get("hasAttachments", False)
                    })
                
                return messages
                
        except Exception as e:
            logger.error(f"Error getting inbox: {str(e)}")
            return []
    
    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """
        Get a specific message by ID.
        
        Args:
            message_id: Message ID
            
        Returns:
            Message data
        """
        if not self.access_token:
            if not await self.authenticate():
                return {}
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Get the message with full content
                response = await client.get(
                    f"{self.GRAPH_API_ENDPOINT}/me/messages/{message_id}",
                    headers=headers,
                    params={
                        "$select": "id,subject,from,toRecipients,ccRecipients,receivedDateTime,body,bodyPreview,conversationId"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get message {message_id}: {response.text}")
                    return {}
                
                msg_data = response.json()
                
                # Format the message
                message = {
                    "id": msg_data.get("id", ""),
                    "thread_id": msg_data.get("conversationId", ""),
                    "subject": msg_data.get("subject", "(No subject)"),
                    "from": msg_data.get("from", {}).get("emailAddress", {}).get("address", ""),
                    "to": ", ".join([r.get("emailAddress", {}).get("address", "") 
                                     for r in msg_data.get("toRecipients", [])]),
                    "cc": ", ".join([r.get("emailAddress", {}).get("address", "") 
                                     for r in msg_data.get("ccRecipients", [])]),
                    "date": msg_data.get("receivedDateTime", ""),
                    "body": msg_data.get("body", {}).get("content", ""),
                    "content_type": msg_data.get("body", {}).get("contentType", "text"),
                    "snippet": msg_data.get("bodyPreview", "")
                }
                
                return message
                
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {str(e)}")
            return {}
    
    async def send_message(self, to: List[str], subject: str, body: str, 
                           cc: Optional[List[str]] = None,
                           bcc: Optional[List[str]] = None) -> bool:
        """
        Send a new message.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body (text)
            cc: List of CC recipients
            bcc: List of BCC recipients
            
        Returns:
            True if successful, False otherwise
        """
        if not self.access_token:
            if not await self.authenticate():
                return False
        
        try:
            # Format recipients
            to_recipients = [{"emailAddress": {"address": email}} for email in to]
            cc_recipients = [{"emailAddress": {"address": email}} for email in cc] if cc else []
            bcc_recipients = [{"emailAddress": {"address": email}} for email in bcc] if bcc else []
            
            # Create message payload
            message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "text",
                        "content": body
                    },
                    "toRecipients": to_recipients,
                    "ccRecipients": cc_recipients,
                    "bccRecipients": bcc_recipients
                }
            }
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Send the message
                response = await client.post(
                    f"{self.GRAPH_API_ENDPOINT}/me/sendMail",
                    headers=headers,
                    json=message
                )
                
                if response.status_code in (202, 204):  # Success codes for sendMail
                    logger.info("Message sent successfully")
                    return True
                else:
                    logger.error(f"Failed to send message: {response.text}")
                    return False
                
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    async def reply_to_message(self, message_id: str, body: str) -> bool:
        """
        Reply to a specific message.
        
        Args:
            message_id: Message ID to reply to
            body: Reply body text
            
        Returns:
            True if successful, False otherwise
        """
        if not self.access_token:
            if not await self.authenticate():
                return False
        
        try:
            # Get the original message first to extract necessary data
            original = await self.get_message(message_id)
            if not original:
                logger.error(f"Could not find original message {message_id}")
                return False
            
            # Create reply payload
            reply = {
                "message": {
                    "body": {
                        "contentType": "text",
                        "content": body
                    }
                }
            }
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Create a reply
                response = await client.post(
                    f"{self.GRAPH_API_ENDPOINT}/me/messages/{message_id}/reply",
                    headers=headers,
                    json=reply
                )
                
                if response.status_code in (202, 204):  # Success codes for reply
                    logger.info("Reply sent successfully")
                    return True
                else:
                    logger.error(f"Failed to send reply: {response.text}")
                    return False
                
        except Exception as e:
            logger.error(f"Error sending reply: {str(e)}")
            return False
    
    async def search_messages(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for messages.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching messages
        """
        if not self.access_token:
            if not await self.authenticate():
                return []
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Search messages using Microsoft Graph search syntax
                # https://docs.microsoft.com/en-us/graph/search-query-parameter
                response = await client.get(
                    f"{self.GRAPH_API_ENDPOINT}/me/messages",
                    headers=headers,
                    params={
                        "$search": f'"{query}"',
                        "$top": limit,
                        "$orderby": "receivedDateTime desc",
                        "$select": "id,subject,from,toRecipients,receivedDateTime,bodyPreview"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to search messages: {response.text}")
                    return []
                
                data = response.json()
                messages = []
                
                for msg_data in data.get("value", []):
                    # Format the message data
                    messages.append({
                        "id": msg_data.get("id", ""),
                        "subject": msg_data.get("subject", "(No subject)"),
                        "from": msg_data.get("from", {}).get("emailAddress", {}).get("address", ""),
                        "to": ", ".join([r.get("emailAddress", {}).get("address", "") 
                                         for r in msg_data.get("toRecipients", [])]),
                        "date": msg_data.get("receivedDateTime", ""),
                        "snippet": msg_data.get("bodyPreview", "")
                    })
                
                return messages
                
        except Exception as e:
            logger.error(f"Error searching messages: {str(e)}")
            return []
    
    async def get_folders(self) -> List[Dict[str, Any]]:
        """
        Get mail folders.
        
        Returns:
            List of folder metadata
        """
        if not self.access_token:
            if not await self.authenticate():
                return []
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Get mail folders
                response = await client.get(
                    f"{self.GRAPH_API_ENDPOINT}/me/mailFolders",
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get folders: {response.text}")
                    return []
                
                data = response.json()
                folders = []
                
                for folder_data in data.get("value", []):
                    folders.append({
                        "id": folder_data.get("id", ""),
                        "name": folder_data.get("displayName", ""),
                        "total_items": folder_data.get("totalItemCount", 0),
                        "unread_items": folder_data.get("unreadItemCount", 0)
                    })
                
                return folders
                
        except Exception as e:
            logger.error(f"Error getting folders: {str(e)}")
            return []


# Factory function to get the appropriate provider
def get_mail_provider(provider_type: str = "gmail", **kwargs) -> Optional[MailProvider]:
    """
    Factory function to create a mail provider instance.
    
    Args:
        provider_type: Type of provider to create (gmail, outlook, etc.)
        **kwargs: Provider-specific arguments
        
    Returns:
        Provider instance or None if invalid type
    """
    if provider_type.lower() == "gmail":
        return GmailProvider(**kwargs)
    elif provider_type.lower() == "outlook":
        return OutlookProvider(**kwargs)
    
    # Add more providers as implemented
    
    logger.error(f"Unsupported mail provider type: {provider_type}")
    return None