"""
Email Service for Turbo Air Equipment Viewer
Handles email sending with Gmail SMTP
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
import json

# Email Configuration
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'turboairquotes@gmail.com',
    'sender_password': 'vbdu njga wymp ufxf'
}

class EmailService:
    def __init__(self):
        """Initialize email service with hardcoded config"""
        self.smtp_server = EMAIL_CONFIG['smtp_server']
        self.smtp_port = EMAIL_CONFIG['smtp_port']
        self.sender_email = EMAIL_CONFIG['sender_email']
        self.sender_password = EMAIL_CONFIG['sender_password']
    
    def send_quote_email(self, recipient_email: str, quote_data: Dict, 
                        items_df: pd.DataFrame, client_data: Dict) -> tuple[bool, str]:
        """Send quote email with CSV and PDF attachments"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Turbo Air Quote {quote_data['quote_number']} - {client_data.get('company', 'Your Company')}"
            
            # Email body
            body = f"""
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
                        <li>CSV file for spreadsheet analysis</li>
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
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Import export functions
            from .export import export_quote_to_csv, export_quote_to_pdf
            
            # Attach CSV
            csv_buffer = export_quote_to_csv(quote_data, items_df, client_data)
            csv_attachment = MIMEBase('text', 'csv')
            csv_attachment.set_payload(csv_buffer.read())
            encoders.encode_base64(csv_attachment)
            csv_attachment.add_header('Content-Disposition', f'attachment; filename="Quote_{quote_data["quote_number"]}.csv"')
            msg.attach(csv_attachment)
            
            # Attach PDF
            pdf_buffer = export_quote_to_pdf(quote_data, items_df, client_data)
            pdf_attachment = MIMEBase('application', 'pdf')
            pdf_attachment.set_payload(pdf_buffer.read())
            encoders.encode_base64(pdf_attachment)
            pdf_attachment.add_header('Content-Disposition', f'attachment; filename="Quote_{quote_data["quote_number"]}.pdf"')
            msg.attach(pdf_attachment)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            return True, "Email sent successfully!"
            
        except Exception as e:
            return False, f"Email error: {str(e)}"

def show_email_quote_dialog(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict):
    """Show dialog to email quote"""
    st.markdown("### 📧 Send Quote via Email")
    
    with st.form("email_quote_form"):
        recipient_email = st.text_input(
            "Recipient Email *",
            value=client_data.get('contact_email', ''),
            placeholder="customer@company.com"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            send_button = st.form_submit_button("Send Email", type="primary", use_container_width=True)
        with col2:
            cancel_button = st.form_submit_button("Cancel", use_container_width=True)
        
        if send_button:
            if not recipient_email or '@' not in recipient_email:
                st.error("Please enter a valid email address")
            else:
                with st.spinner("Sending email..."):
                    email_service = EmailService()
                    success, message = email_service.send_quote_email(
                        recipient_email=recipient_email.strip(),
                        quote_data=quote_data,
                        items_df=items_df,
                        client_data=client_data
                    )
                    
                    if success:
                        st.success(message)
                        st.balloons()
                        return True
                    else:
                        st.error(message)
        
        if cancel_button:
            return False
    
    return False