"""
Email functionality for Turbo Air Equipment Viewer
Handles sending quotes via email
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import streamlit as st
from typing import Dict, Tuple, Optional
import pandas as pd
from datetime import datetime
import io

class EmailService:
    def __init__(self):
        """Initialize email service with configuration from secrets"""
        self.configured = False
        try:
            # Get email configuration from Streamlit secrets
            self.smtp_server = st.secrets["email"]["smtp_server"]
            self.smtp_port = int(st.secrets["email"]["smtp_port"])
            self.sender_email = st.secrets["email"]["sender_email"]
            self.sender_password = st.secrets["email"]["sender_password"]
            self.configured = True
        except Exception as e:
            print(f"Email configuration error: {e}")
            self.configured = False
    
    def send_quote_email(self, recipient_email: str, quote_data: Dict, items_df: pd.DataFrame, client_data: Dict) -> Tuple[bool, str]:
        """Send quote via email with PDF attachment"""
        if not self.configured:
            return False, "Email service not configured"
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Quote {quote_data.get('quote_number', 'N/A')} - Turbo Air Equipment"
            
            # Create email body
            body = self._create_email_body(quote_data, items_df, client_data)
            msg.attach(MIMEText(body, 'html'))
            
            # Create PDF attachment
            try:
                from .export import export_quote_to_pdf
                pdf_buffer = export_quote_to_pdf(quote_data, items_df, client_data)
                
                # Attach PDF
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(pdf_buffer.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="Quote_{quote_data.get("quote_number", "N_A")}.pdf"'
                )
                msg.attach(part)
            except Exception as e:
                print(f"Error creating PDF attachment: {e}")
                # Continue without attachment
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, recipient_email, text)
            server.quit()
            
            return True, "Quote sent successfully!"
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False, f"Failed to send email: {str(e)}"
    
    def _create_email_body(self, quote_data: Dict, items_df: pd.DataFrame, client_data: Dict) -> str:
        """Create HTML email body"""
        
        # Calculate totals
        subtotal = float(quote_data.get('subtotal', 0))
        tax_rate = float(quote_data.get('tax_rate', 0))
        if tax_rate > 1:
            tax_rate_display = tax_rate
        else:
            tax_rate_display = tax_rate * 100
        tax_amount = float(quote_data.get('tax_amount', 0))
        total = float(quote_data.get('total_amount', 0))
        
        # Create items table
        items_html = ""
        for idx, item in items_df.iterrows():
            sku = str(item.get('sku', 'Unknown'))
            description = str(item.get('product_type', ''))
            quantity = int(item.get('quantity', 1))
            unit_price = float(item.get('price', 0))
            total_price = unit_price * quantity
            
            items_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{sku}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{description}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">{quantity}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">${unit_price:,.2f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">${total_price:,.2f}</td>
            </tr>
            """
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #20429C; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .quote-info {{ background-color: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background-color: #20429C; color: white; padding: 12px; text-align: left; }}
                .totals {{ margin-top: 20px; }}
                .total-row {{ font-weight: bold; font-size: 1.1em; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>TURBO AIR EQUIPMENT QUOTE</h1>
            </div>
            
            <div class="content">
                <div class="quote-info">
                    <h3>Quote Information</h3>
                    <p><strong>Quote Number:</strong> {quote_data.get('quote_number', 'N/A')}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                    <p><strong>Client:</strong> {client_data.get('company', 'N/A')}</p>
                    <p><strong>Contact:</strong> {client_data.get('contact_name', 'N/A')}</p>
                </div>
                
                <h3>Equipment Details</h3>
                <table>
                    <thead>
                        <tr>
                            <th>SKU</th>
                            <th>Description</th>
                            <th style="text-align: center;">Qty</th>
                            <th style="text-align: right;">Unit Price</th>
                            <th style="text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>
                
                <div class="totals">
                    <table style="width: 300px; margin-left: auto;">
                        <tr>
                            <td style="padding: 5px; text-align: right;"><strong>Subtotal:</strong></td>
                            <td style="padding: 5px; text-align: right;">${subtotal:,.2f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px; text-align: right;"><strong>Tax ({tax_rate_display:.1f}%):</strong></td>
                            <td style="padding: 5px; text-align: right;">${tax_amount:,.2f}</td>
                        </tr>
                        <tr class="total-row" style="border-top: 2px solid #20429C;">
                            <td style="padding: 10px; text-align: right;"><strong>TOTAL:</strong></td>
                            <td style="padding: 10px; text-align: right;"><strong>${total:,.2f}</strong></td>
                        </tr>
                    </table>
                </div>
                
                <div class="footer">
                    <p>Thank you for choosing Turbo Air Equipment!</p>
                    <p>This quote is valid for 30 days from the date of issue.</p>
                    <p>If you have any questions, please don't hesitate to contact us.</p>
                    <br>
                    <p><strong>Turbo Air Equipment</strong><br>
                    Email: {self.sender_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_body

def show_email_quote_dialog(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict):
    """Show email quote dialog - MISSING FUNCTION ADDED"""
    st.markdown("#### Send Quote via Email")
    
    # Email input
    recipient_email = st.text_input(
        "Recipient Email:", 
        value=client_data.get('contact_email', ''),
        placeholder="Enter recipient email address"
    )
    
    # Additional message
    additional_message = st.text_area(
        "Additional Message (optional):",
        placeholder="Add any additional notes or message..."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Send Email", type="primary", use_container_width=True):
            if recipient_email and '@' in recipient_email:
                email_service = EmailService()
                if email_service.configured:
                    with st.spinner("Sending email..."):
                        success, message = email_service.send_quote_email(
                            recipient_email, quote_data, items_df, client_data
                        )
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("Email service not configured. Please check your secrets.")
            else:
                st.error("Please enter a valid email address")
    
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def get_email_service() -> Optional[EmailService]:
    """Get email service instance - MISSING FUNCTION ADDED"""
    try:
        return EmailService()
    except Exception as e:
        print(f"Error creating email service: {e}")
        return None