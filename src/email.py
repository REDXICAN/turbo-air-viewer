"""
Fixed Email Service for Turbo Air Equipment Viewer
Fixes authentication and email sending issues
"""

import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict
import io
from datetime import datetime
import pandas as pd
import socket

def is_email_configured() -> bool:
    """Check if email service is configured"""
    try:
        email_config = st.secrets.get('email', {})
        required_fields = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password']
        return all(email_config.get(field) for field in required_fields)
    except:
        return False

class EmailService:
    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str):
        """Initialize email service"""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.configured = all([smtp_server, smtp_port, sender_email, sender_password])
    
    def test_connection(self) -> tuple[bool, str]:
        """Test SMTP connection with better error handling"""
        if not self.configured:
            return False, "Email service not configured"
        
        try:
            # Test connection with longer timeout
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15) as server:
                server.set_debuglevel(0)  # Disable debug output
                server.starttls()
                server.login(self.sender_email, self.sender_password)
            return True, "Connection successful"
        except smtplib.SMTPAuthenticationError as e:
            return False, f"Authentication failed: {str(e)}. Check your email and app password."
        except smtplib.SMTPConnectError as e:
            return False, f"Cannot connect to {self.smtp_server}:{self.smtp_port}. Error: {str(e)}"
        except socket.timeout:
            return False, "Connection timed out. Check your internet connection."
        except socket.gaierror as e:
            return False, f"DNS resolution failed: {str(e)}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def send_quote_email(self, recipient_email: str, quote_data: Dict, 
                        client_data: Dict, attachments: Dict[str, io.BytesIO]) -> tuple[bool, str]:
        """Send quote email with attachments - improved error handling"""
        if not self.configured:
            return False, "Email service is not configured"
        
        # Validate email address
        if '@' not in recipient_email or '.' not in recipient_email.split('@')[1]:
            return False, "Invalid recipient email address"
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Turbo Air Quote {quote_data['quote_number']} - {client_data.get('company', 'Your Company')}"
            
            # Email body with better formatting
            body_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
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
                            <li><strong>Subtotal:</strong> ${quote_data.get('subtotal', 0):,.2f}</li>
                            <li><strong>Tax:</strong> ${quote_data.get('tax_amount', 0):,.2f}</li>
                            <li><strong>Total Amount:</strong> ${quote_data.get('total_amount', 0):,.2f}</li>
                            <li><strong>Valid Until:</strong> {(datetime.now() + pd.Timedelta(days=30)).strftime('%B %d, %Y')}</li>
                        </ul>
                    </div>
                    
                    <p>The attached files include:</p>
                    <ul>
                        <li>Excel spreadsheet with detailed product information and images</li>
                        <li>PDF document for easy viewing and printing</li>
                    </ul>
                    
                    {f"<p><strong>Additional Message:</strong><br>{client_data.get('custom_message', '')}</p>" if client_data.get('custom_message') else ""}
                    
                    <p>If you have any questions or would like to proceed with this order, please don't hesitate to contact us.</p>
                    
                    <p>Best regards,<br>
                    The Turbo Air Sales Team<br>
                    Email: {self.sender_email}<br>
                    Phone: 1-800-TURBO-AIR</p>
                </div>
                
                <div style="background-color: #20429c; color: white; padding: 10px; text-align: center; font-size: 12px;">
                    <p style="margin: 0;">This quote is valid for 30 days from the date of issue.</p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body_content, 'html'))
            
            # Add attachments with better error handling
            for filename, file_buffer in attachments.items():
                try:
                    file_buffer.seek(0)
                    
                    # Determine MIME type
                    if filename.endswith('.pdf'):
                        maintype, subtype = 'application', 'pdf'
                    elif filename.endswith('.xlsx'):
                        maintype, subtype = 'application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    else:
                        maintype, subtype = 'application', 'octet-stream'
                    
                    # Create attachment
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(file_buffer.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{filename}"'
                    )
                    msg.attach(part)
                except Exception as e:
                    print(f"Error attaching file {filename}: {e}")
                    # Continue with other attachments
            
            # Send email with better error handling
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.set_debuglevel(0)  # Disable debug output
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                
                # Send to recipient
                server.send_message(msg, to_addrs=[recipient_email])
            
            return True, f"Email sent successfully to {recipient_email}"
                
        except smtplib.SMTPAuthenticationError as e:
            return False, f"Authentication failed: {str(e)}. Please check your Gmail app password."
        except smtplib.SMTPRecipientsRefused as e:
            return False, f"Recipient email rejected: {str(e)}"
        except smtplib.SMTPDataError as e:
            return False, f"Email data error: {str(e)}"
        except socket.timeout:
            return False, "Email sending timed out. Please try again."
        except Exception as e:
            return False, f"Email error: {str(e)}"
    
    def send_test_email(self, recipient_email: str) -> tuple[bool, str]:
        """Send a test email"""
        if not self.configured:
            return False, "Email service is not configured"
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = "Turbo Air - Test Email"
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Test Email from Turbo Air Quote System</h2>
                <p>This is a test email to verify that your email configuration is working correctly.</p>
                <p>If you received this email, your Gmail integration is properly configured!</p>
                <p><strong>Configuration Details:</strong></p>
                <ul>
                    <li>SMTP Server: {self.smtp_server}</li>
                    <li>Port: {self.smtp_port}</li>
                    <li>From: {self.sender_email}</li>
                </ul>
                <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.set_debuglevel(0)
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return True, "Test email sent successfully"
            
        except Exception as e:
            return False, f"Test email error: {str(e)}"

def get_email_service():
    """Get email service instance with better error handling"""
    if not is_email_configured():
        return None
    
    try:
        email_config = st.secrets.get('email', {})
        return EmailService(
            smtp_server=email_config.get('smtp_server', 'smtp.gmail.com'),
            smtp_port=int(email_config.get('smtp_port', 587)),
            sender_email=email_config.get('sender_email', ''),
            sender_password=email_config.get('sender_password', '')
        )
    except Exception as e:
        print(f"Failed to initialize email service: {str(e)}")
        return None

def show_email_quote_dialog(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict):
    """Show dialog to email quote with improved UI and error handling"""
    email_service = get_email_service()
    
    if not email_service or not email_service.configured:
        st.error("❌ Email service is not configured properly")
        st.info("To enable email functionality, check your secrets configuration:")
        st.code("""
[email]
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "turboairquotes@gmail.com"
sender_password = "your-app-password"
        """)
        return False
    
    # Test connection first
    with st.expander("🔧 Email Configuration Test", expanded=False):
        if st.button("Test Email Configuration"):
            with st.spinner("Testing email connection..."):
                connection_ok, connection_msg = email_service.test_connection()
                if connection_ok:
                    st.success(f"✅ {connection_msg}")
                else:
                    st.error(f"❌ {connection_msg}")
                    
                    # Show troubleshooting info
                    st.warning("Common Gmail setup issues:")
                    st.write("1. Enable 2-factor authentication on your Gmail account")
                    st.write("2. Generate an App Password (not your regular Gmail password)")
                    st.write("3. Use the 16-character app password in your secrets")
                    st.write("4. Make sure 'Less secure app access' is enabled if not using 2FA")
    
    # Create email dialog
    with st.expander("📧 Email Quote", expanded=True):
        with st.form("email_quote_form"):
            st.subheader("Send Quote via Email")
            
            # Pre-fill with client email if available
            default_email = client_data.get('contact_email', '')
            recipient_email = st.text_input(
                "Recipient Email*", 
                value=default_email,
                help="Enter the email address to send the quote to"
            )
            
            # Additional recipients
            cc_emails = st.text_input(
                "CC (optional)", 
                placeholder="separate multiple emails with commas",
                help="Additional recipients who will receive a copy"
            )
            
            # Custom message
            custom_message = st.text_area(
                "Personal Message (optional)",
                placeholder="Add any additional notes or messages here...",
                height=100,
                help="This message will be included in the email body"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                send_button = st.form_submit_button("📧 Send Email", type="primary", use_container_width=True)
            with col2:
                cancel_button = st.form_submit_button("Cancel", use_container_width=True)
            
            if send_button:
                if not recipient_email:
                    st.error("❌ Please enter a recipient email address")
                    return False
                
                if not recipient_email.count('@') == 1 or '.' not in recipient_email.split('@')[1]:
                    st.error("❌ Please enter a valid email address")
                    return False
                
                with st.spinner("Sending email..."):
                    try:
                        # Prepare attachments
                        from .export import prepare_email_attachments
                        attachments = prepare_email_attachments(quote_data, items_df, client_data)
                        
                        if not attachments:
                            st.error("❌ Could not prepare email attachments")
                            return False
                        
                        # Add custom message to client data if provided
                        if custom_message:
                            client_data['custom_message'] = custom_message
                        
                        # Send email
                        success, message = email_service.send_quote_email(
                            recipient_email=recipient_email,
                            quote_data=quote_data,
                            client_data=client_data,
                            attachments=attachments
                        )
                        
                        if success:
                            st.success(f"✅ Quote emailed successfully to {recipient_email}!")
                            st.info(f"📋 Quote #{quote_data['quote_number']} sent with Excel and PDF attachments")
                            st.balloons()
                            return True
                        else:
                            st.error(f"❌ Failed to send email: {message}")
                            return False
                            
                    except Exception as e:
                        st.error(f"❌ Email system error: {str(e)}")
                        return False
            
            if cancel_button:
                return False