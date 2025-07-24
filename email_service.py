"""
Email Service for Turbo Air Equipment Viewer
Handles sending quotes via Microsoft 365 Graph API
"""

import streamlit as st
from msal import ConfidentialClientApplication
import requests
import base64
from typing import Dict, List
import io
from datetime import datetime
import pandas as pd

class EmailService:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, sender_email: str):
        """Initialize email service with Microsoft 365 credentials"""
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.sender_email = sender_email
        
        # Initialize MSAL app
        self.app = ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret
        )
        
        self.graph_url = "https://graph.microsoft.com/v1.0"
        self.scope = ["https://graph.microsoft.com/.default"]
    
    def _get_access_token(self) -> str:
        """Get access token for Microsoft Graph API"""
        result = self.app.acquire_token_silent(self.scope, account=None)
        
        if not result:
            result = self.app.acquire_token_for_client(scopes=self.scope)
        
        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception(f"Could not acquire token: {result.get('error')}")
    
    def send_quote_email(self, recipient_email: str, quote_data: Dict, 
                        client_data: Dict, attachments: Dict[str, io.BytesIO]) -> bool:
        """Send quote email with attachments"""
        try:
            access_token = self._get_access_token()
            
            # Prepare email content
            subject = f"Turbo Air Quote {quote_data['quote_number']} - {client_data.get('company', 'Your Company')}"
            
            body_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #20429c; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0;">Turbo Air Equipment Quote</h1>
                    </div>
                    
                    <div style="padding: 20px;">
                        <p>Dear {client_data.get('contact_name', 'Valued Customer')},</p>
                        
                        <p>Thank you for your interest in Turbo Air equipment. Please find attached your quote 
                        <strong>{quote_data['quote_number']}</strong> dated {datetime.now().strftime('%B %d, %Y')}.</p>
                        
                        <div style="background-color: #f0f0f0; padding: 15px; margin: 20px 0; border-radius: 5px;">
                            <h3 style="margin-top: 0;">Quote Summary:</h3>
                            <ul style="list-style: none; padding: 0;">
                                <li><strong>Quote Number:</strong> {quote_data['quote_number']}</li>
                                <li><strong>Total Amount:</strong> ${quote_data['total_amount']:,.2f}</li>
                                <li><strong>Valid Until:</strong> {(datetime.now() + pd.Timedelta(days=30)).strftime('%B %d, %Y')}</li>
                            </ul>
                        </div>
                        
                        <p>The attached files include:</p>
                        <ul>
                            <li>Excel spreadsheet with detailed product information</li>
                            <li>PDF document for easy viewing and printing</li>
                        </ul>
                        
                        <p>If you have any questions or would like to proceed with this order, please don't hesitate to contact us.</p>
                        
                        <p>Best regards,<br>
                        The Turbo Air Sales Team<br>
                        Email: {self.sender_email}<br>
                        Phone: 1-800-TURBO-AIR</p>
                    </div>
                    
                    <div style="background-color: #20429c; color: white; padding: 10px; text-align: center; font-size: 12px;">
                        <p style="margin: 0;">This quote is valid for 30 days from the date of issue.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Prepare email message
            message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": body_content
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": recipient_email
                            }
                        }
                    ],
                    "attachments": []
                }
            }
            
            # Add attachments
            for filename, file_buffer in attachments.items():
                file_buffer.seek(0)
                file_content = file_buffer.read()
                
                attachment = {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": filename,
                    "contentType": "application/octet-stream",
                    "contentBytes": base64.b64encode(file_content).decode('utf-8')
                }
                
                message["message"]["attachments"].append(attachment)
            
            # Send email
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            send_url = f"{self.graph_url}/users/{self.sender_email}/sendMail"
            
            response = requests.post(send_url, headers=headers, json=message)
            
            if response.status_code == 202:
                return True
            else:
                raise Exception(f"Failed to send email: {response.status_code} - {response.text}")
                
        except Exception as e:
            st.error(f"Email error: {str(e)}")
            return False
    
    def send_test_email(self, recipient_email: str) -> bool:
        """Send a test email to verify configuration"""
        try:
            access_token = self._get_access_token()
            
            message = {
                "message": {
                    "subject": "Turbo Air - Test Email",
                    "body": {
                        "contentType": "HTML",
                        "content": """
                        <html>
                        <body>
                            <h2>Test Email from Turbo Air Quote System</h2>
                            <p>This is a test email to verify that your email configuration is working correctly.</p>
                            <p>If you received this email, your Microsoft 365 integration is properly configured!</p>
                        </body>
                        </html>
                        """
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": recipient_email
                            }
                        }
                    ]
                }
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            send_url = f"{self.graph_url}/users/{self.sender_email}/sendMail"
            
            response = requests.post(send_url, headers=headers, json=message)
            
            return response.status_code == 202
            
        except Exception as e:
            st.error(f"Test email error: {str(e)}")
            return False

# Helper function to initialize email service
def get_email_service():
    """Get email service instance from secrets"""
    if 'email' not in st.secrets:
        return None
    
    try:
        email_config = st.secrets['email']
        return EmailService(
            tenant_id=email_config['tenant_id'],
            client_id=email_config['client_id'],
            client_secret=email_config['client_secret'],
            sender_email=email_config['sender_email']
        )
    except Exception as e:
        st.error(f"Failed to initialize email service: {str(e)}")
        return None

# UI Components for email functionality
def show_email_quote_dialog(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict):
    """Show dialog to email quote"""
    import pandas as pd
    from export_utils import prepare_email_attachments
    
    with st.form("email_quote_form"):
        st.subheader("Email Quote")
        
        # Pre-fill with client email if available
        default_email = client_data.get('contact_email', '')
        recipient_email = st.text_input("Recipient Email", value=default_email)
        
        # Additional recipients
        cc_emails = st.text_input("CC (separate multiple emails with commas)", "")
        
        # Custom message
        custom_message = st.text_area(
            "Add a personal message (optional)",
            placeholder="Add any additional notes or messages here..."
        )
        
        col1, col2 = st.columns(2)
        with col1:
            send_button = st.form_submit_button("Send Email", type="primary", use_container_width=True)
        with col2:
            cancel_button = st.form_submit_button("Cancel", use_container_width=True)
        
        if send_button and recipient_email:
            email_service = get_email_service()
            
            if not email_service:
                st.error("Email service not configured. Please check your settings.")
                return False
            
            with st.spinner("Sending email..."):
                # Prepare attachments
                attachments = prepare_email_attachments(quote_data, items_df, client_data)
                
                # Add custom message to client data if provided
                if custom_message:
                    client_data['custom_message'] = custom_message
                
                # Send email
                success = email_service.send_quote_email(
                    recipient_email=recipient_email,
                    quote_data=quote_data,
                    client_data=client_data,
                    attachments=attachments
                )
                
                if success:
                    st.success(f"Quote emailed successfully to {recipient_email}!")
                    return True
                else:
                    st.error("Failed to send email. Please try again.")
                    return False
        
        return cancel_button