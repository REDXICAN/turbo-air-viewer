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
import ssl

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
            
            # Optional: SSL mode (default to True for security)
            self.use_ssl = st.secrets["email"].get("use_ssl", True)
            
            self.configured = True
            st.success(f"Email configured: {self.sender_email} via {self.smtp_server}:{self.smtp_port}")
            
        except KeyError as e:
            st.error(f"Missing email configuration key: {e}")
            st.error("Required keys: smtp_server, smtp_port, sender_email, sender_password")
            self.configured = False
        except Exception as e:
            st.error(f"Email configuration error: {e}")
            self.configured = False
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test SMTP connection"""
        if not self.configured:
            return False, "Email service not configured"
        
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            if self.smtp_port == 465:  # SSL
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
                server.login(self.sender_email, self.sender_password)
            else:  # TLS (port 587)
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
            
            server.quit()
            return True, "SMTP connection successful"
            
        except smtplib.SMTPAuthenticationError as e:
            return False, f"Authentication failed: {e}. Check your app password."
        except smtplib.SMTPConnectError as e:
            return False, f"Connection failed: {e}. Check server and port."
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    def send_quote_email(self, recipient_email: str, quote_data: Dict, items_df: pd.DataFrame, client_data: Dict, additional_message: str = "") -> Tuple[bool, str]:
        """Send quote via email with PDF attachment"""
        if not self.configured:
            return False, "Email service not configured"
        
        # First test connection
        conn_success, conn_msg = self.test_connection()
        if not conn_success:
            return False, f"Connection test failed: {conn_msg}"
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')  # Support both HTML and plain text
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Quote {quote_data.get('quote_number', 'N/A')} - Turbo Air Equipment"
            
            # Create email body
            html_body = self._create_email_body(quote_data, items_df, client_data, additional_message)
            plain_body = self._create_plain_text_body(quote_data, items_df, client_data, additional_message)
            
            # Attach both plain text and HTML versions
            msg.attach(MIMEText(plain_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Create PDF attachment (optional - remove if export module doesn't exist)
            try:
                from .export import export_quote_to_pdf
                pdf_buffer = export_quote_to_pdf(quote_data, items_df, client_data)
                
                # Attach PDF
                part = MIMEBase('application', 'pdf')
                part.set_payload(pdf_buffer.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="Quote_{quote_data.get("quote_number", "N_A")}.pdf"'
                )
                msg.attach(part)
            except ImportError:
                st.info("PDF export module not available - sending without attachment")
            except Exception as e:
                st.warning(f"Could not attach PDF: {e}")
            
            # Send email with proper SSL/TLS handling
            context = ssl.create_default_context()
            
            if self.smtp_port == 465:  # Gmail SSL
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:  # Gmail TLS (port 587)
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls(context=context)
            
            server.login(self.sender_email, self.sender_password)
            
            # Send the email
            failed_recipients = server.sendmail(self.sender_email, [recipient_email], msg.as_string())
            server.quit()
            
            if failed_recipients:
                return False, f"Failed to send to: {failed_recipients}"
            
            return True, f"Quote sent successfully to {recipient_email}!"
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Authentication failed: {str(e)}. Please check your app password."
            st.error(error_msg)
            return False, error_msg
        except smtplib.SMTPRecipientsRefused as e:
            error_msg = f"Recipient email refused: {str(e)}"
            st.error(error_msg)
            return False, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            st.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            st.error(error_msg)
            return False, error_msg
    
    def _create_plain_text_body(self, quote_data: Dict, items_df: pd.DataFrame, client_data: Dict, additional_message: str = "") -> str:
        """Create plain text email body as fallback"""
        # Calculate totals
        subtotal = float(quote_data.get('subtotal', 0))
        tax_rate = float(quote_data.get('tax_rate', 0))
        if tax_rate > 1:
            tax_rate_display = tax_rate
        else:
            tax_rate_display = tax_rate * 100
        tax_amount = float(quote_data.get('tax_amount', 0))
        total = float(quote_data.get('total_amount', 0))
        
        # Create items list
        items_text = ""
        for idx, item in items_df.iterrows():
            sku = str(item.get('sku', 'Unknown'))
            description = str(item.get('product_type', ''))
            quantity = int(item.get('quantity', 1))
            unit_price = float(item.get('price', 0))
            total_price = unit_price * quantity
            
            items_text += f"{sku} - {description} - Qty: {quantity} - ${unit_price:,.2f} each - Total: ${total_price:,.2f}\n"
        
        plain_body = f"""
TURBO AIR EQUIPMENT - QUOTE

{additional_message if additional_message else ''}

Quote Information:
- Quote Number: {quote_data.get('quote_number', 'N/A')}
- Date: {datetime.now().strftime('%B %d, %Y')}
- Client: {client_data.get('company', 'N/A')}
- Contact: {client_data.get('contact_name', 'N/A')}

Equipment Details:
{items_text}

Totals:
Subtotal: ${subtotal:,.2f}
Tax ({tax_rate_display:.1f}%): ${tax_amount:,.2f}
TOTAL: ${total:,.2f}

Thank you for choosing Turbo Air Equipment!
This quote is valid for 30 days from the date of issue.

Turbo Air Equipment
Email: {self.sender_email}
        """
        
        return plain_body
    
    def _create_email_body(self, quote_data: Dict, items_df: pd.DataFrame, client_data: Dict, additional_message: str = "") -> str:
        """Create HTML email body with logo"""
        import base64
        import os
        
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
        
        # Add additional message section if provided
        additional_section = ""
        if additional_message:
            additional_section = f"""
            <div class="additional-message" style="background-color: #e8f4f8; padding: 15px; margin: 20px 0; border-radius: 5px; border-left: 4px solid #20429C;">
                <h4>Additional Message:</h4>
                <p>{additional_message.replace('\n', '<br>')}</p>
            </div>
            """
        
        # Try to load and encode the logo
        logo_html = ""
        try:
            logo_path = "Turboair_Logo_01.png"
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as logo_file:
                    logo_base64 = base64.b64encode(logo_file.read()).decode()
                logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="Turbo Air Logo" style="max-width: 300px; height: auto;">'
            else:
                logo_html = '<h1 style="color: white; margin: 0;">TURBO AIR EQUIPMENT</h1>'
        except Exception as e:
            logo_html = '<h1 style="color: white; margin: 0;">TURBO AIR EQUIPMENT</h1>'
        
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
                {logo_html}
                <h2 style="margin-top: 10px; margin-bottom: 0;">EQUIPMENT QUOTE</h2>
            </div>
            
            <div class="content">
                {additional_section}
                
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
    """Show email quote dialog with proper state management"""
    st.markdown("#### Send Quote via Email")
    
    # Test connection first
    email_service = EmailService()
    if email_service.configured:
        with st.expander("Test Email Connection", expanded=False):
            if st.button("Test SMTP Connection"):
                with st.spinner("Testing connection..."):
                    success, message = email_service.test_connection()
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # Use form to prevent collapse issues
    with st.form("email_quote_form", clear_on_submit=False):
        # Email input
        recipient_email = st.text_input(
            "Recipient Email:", 
            value=client_data.get('contact_email', ''),
            placeholder="Enter recipient email address"
        )
        
        # Additional message
        additional_message = st.text_area(
            "Additional Message (optional):",
            placeholder="Add any additional notes or message...",
            height=100
        )
        
        # Form buttons
        col1, col2 = st.columns(2)
        
        with col1:
            send_email = st.form_submit_button("Send Email", type="primary", use_container_width=True)
        
        with col2:
            cancel_email = st.form_submit_button("Cancel", use_container_width=True)
    
    # Handle form submission
    if send_email:
        if recipient_email and '@' in recipient_email:
            if email_service.configured:
                with st.spinner("Sending email..."):
                    success, message = email_service.send_quote_email(
                        recipient_email, quote_data, items_df, client_data, additional_message
                    )
                
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)
            else:
                st.error("Email service not configured. Please check your secrets.")
        else:
            st.error("Please enter a valid email address")
    
    if cancel_email:
        st.info("Email cancelled.")

def test_email_connection():
    """Test email connection - for debugging"""
    email_service = EmailService()
    return email_service.test_connection()

def get_email_service() -> Optional[EmailService]:
    """Get email service instance"""
    try:
        return EmailService()
    except Exception as e:
        st.error(f"Error creating email service: {e}")
        return None