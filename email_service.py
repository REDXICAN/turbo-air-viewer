"""
Email Service for Turbo Air Equipment Viewer
Handles sending quotes via Gmail SMTP
"""

import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64
from typing import Dict, List
import io
from datetime import datetime
import pandas as pd
import os

# Check if email service is configured
def is_email_configured():
    """Check if email service credentials are configured"""
    try:
        # Try Streamlit secrets first
        if hasattr(st, 'secrets') and 'email' in st.secrets:
            return bool(st.secrets['email'].get('sender_email') and 
                       st.secrets['email'].get('sender_password'))
        else:
            # Try environment variables
            from dotenv import load_dotenv
            load_dotenv()
            return bool(os.getenv('EMAIL_SENDER') and 
                       os.getenv('EMAIL_PASSWORD'))
    except:
        return False

class EmailService:
    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str):
        """Initialize email service with Gmail credentials"""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        
        # Check if credentials are provided
        if all([smtp_server, smtp_port, sender_email, sender_password]):
            self.configured = True
        else:
            self.configured = False
    
    def send_quote_email(self, recipient_email: str, quote_data: Dict, 
                        client_data: Dict, attachments: Dict[str, io.BytesIO]) -> bool:
        """Send quote email with attachments"""
        if not self.configured:
            st.error("Email service is not configured. Please add email credentials.")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Turbo Air Quote {quote_data['quote_number']} - {client_data.get('company', 'Your Company')}"
            
            # Email body
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
            
            msg.attach(MIMEText(body_content, 'html'))
            
            # Add attachments
            for filename, file_buffer in attachments.items():
                file_buffer.seek(0)
                
                # Create attachment
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file_buffer.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return True
                
        except Exception as e:
            st.error(f"Email error: {str(e)}")
            return False
    
    def send_test_email(self, recipient_email: str) -> bool:
        """Send a test email to verify configuration"""
        if not self.configured:
            st.error("Email service is not configured")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = "Turbo Air - Test Email"
            
            body = """
            <html>
            <body>
                <h2>Test Email from Turbo Air Quote System</h2>
                <p>This is a test email to verify that your email configuration is working correctly.</p>
                <p>If you received this email, your Gmail integration is properly configured!</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            st.error(f"Test email error: {str(e)}")
            return False

# Helper function to initialize email service
def get_email_service():
    """Get email service instance from secrets or environment variables"""
    if not is_email_configured():
        return None
    
    try:
        # Try Streamlit secrets first
        if hasattr(st, 'secrets') and 'email' in st.secrets:
            email_config = st.secrets['email']
            return EmailService(
                smtp_server=email_config.get('smtp_server', 'smtp.gmail.com'),
                smtp_port=email_config.get('smtp_port', 587),
                sender_email=email_config.get('sender_email', ''),
                sender_password=email_config.get('sender_password', '')
            )
        else:
            # Try environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            return EmailService(
                smtp_server=os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
                smtp_port=int(os.getenv('EMAIL_SMTP_PORT', '587')),
                sender_email=os.getenv('EMAIL_SENDER', ''),
                sender_password=os.getenv('EMAIL_PASSWORD', '')
            )
    except Exception as e:
        print(f"Failed to initialize email service: {str(e)}")
        return None

# UI Components for email functionality
def show_email_quote_dialog(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict):
    """Show dialog to email quote"""
    email_service = get_email_service()
    
    if not email_service or not email_service.configured:
        st.warning("Email service is not configured. Quote cannot be sent via email.")
        st.info("To enable email functionality, configure Gmail credentials in your secrets.")
        return
    
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