"""
Email functionality for Turbo Air Equipment Viewer
Handles quote email sending with CC support, improved error handling and production-ready features
"""

import streamlit as st
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from typing import Dict, Tuple
import io

class EmailService:
    """Email service class for handling SMTP operations with CC support"""
    
    def __init__(self):
        """Initialize email service with configuration from secrets"""
        try:
            # Load email configuration from Streamlit secrets
            self.smtp_server = st.secrets.get("email", {}).get("smtp_server", "")
            self.smtp_port = int(st.secrets.get("email", {}).get("smtp_port", 587))
            self.sender_email = st.secrets.get("email", {}).get("sender_email", "")
            self.sender_password = st.secrets.get("email", {}).get("sender_password", "")
            
            # Check if all required settings are present
            self.configured = bool(
                self.smtp_server and 
                self.smtp_port and 
                self.sender_email and 
                self.sender_password
            )
            
        except Exception as e:
            st.error(f"Error loading email configuration: {str(e)}")
            self.configured = False
            self.smtp_server = ""
            self.smtp_port = 587
            self.sender_email = ""
            self.sender_password = ""
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test SMTP connection with detailed error reporting"""
        if not self.configured:
            return False, "Email service not configured - check secrets.toml"
        
        try:
            # Create SMTP connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.set_debuglevel(0)  # Turn off debug output
            
            # Start TLS encryption
            server.starttls()
            
            # Login with credentials
            server.login(self.sender_email, self.sender_password)
            
            # If we get here, connection is successful
            server.quit()
            return True, "SMTP connection successful!"
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = str(e)
            if "Username and Password not accepted" in error_msg:
                return False, "Authentication failed: Check your app password (not regular Gmail password)"
            elif "534-5.7.9" in error_msg or "534-5.7.14" in error_msg:
                return False, "Authentication failed: Enable 2FA and use app password"
            else:
                return False, f"Authentication error: {error_msg}"
                
        except smtplib.SMTPConnectError as e:
            return False, f"Connection error: Cannot connect to {self.smtp_server}:{self.smtp_port}"
            
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
            
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def send_quote_email_with_cc(self, recipient_email: str, quote_data: Dict, items_df: pd.DataFrame, 
                        client_data: Dict, cc_email: str = None, additional_message: str = "", 
                        attach_pdf: bool = True, attach_excel: bool = False) -> Tuple[bool, str]:
        """Send quote email with CC support and attachments"""
        
        if not self.configured:
            return False, "Email service not configured"
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            if cc_email:
                msg['Cc'] = cc_email
            msg['Subject'] = f"Quote {quote_data.get('quote_number', 'N/A')} - Turbo Air Equipment"
            
            # Create email body
            body = self._create_email_body(quote_data, items_df, client_data, additional_message)
            msg.attach(MIMEText(body, 'html'))
            
            # Add PDF attachment if requested
            if attach_pdf:
                try:
                    from .export import generate_pdf_quote
                    pdf_buffer = generate_pdf_quote(quote_data, items_df, client_data)
                    
                    pdf_attachment = MIMEApplication(pdf_buffer.getvalue(), _subtype='pdf')
                    pdf_attachment.add_header('Content-Disposition', 'attachment', 
                                            filename=f"Quote_{quote_data.get('quote_number', 'N/A')}.pdf")
                    msg.attach(pdf_attachment)
                    
                except Exception as e:
                    st.warning(f"Could not attach PDF: {str(e)}")
            
            # Add Excel attachment if requested
            if attach_excel:
                try:
                    from .export import generate_excel_quote
                    excel_buffer = generate_excel_quote(quote_data, items_df, client_data)
                    
                    excel_attachment = MIMEApplication(excel_buffer.getvalue(), 
                                                     _subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    excel_attachment.add_header('Content-Disposition', 'attachment', 
                                              filename=f"Quote_{quote_data.get('quote_number', 'N/A')}.xlsx")
                    msg.attach(excel_attachment)
                    
                except Exception as e:
                    st.warning(f"Could not attach Excel: {str(e)}")
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            # Prepare recipient list (To + CC)
            recipients = [recipient_email]
            if cc_email:
                recipients.append(cc_email)
            
            text = msg.as_string()
            server.sendmail(self.sender_email, recipients, text)
            server.quit()
            
            # Create success message
            success_msg = f"Quote sent successfully to {recipient_email}"
            if cc_email:
                success_msg += f" (CC: {cc_email})"
                
            return True, success_msg
            
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def send_quote_email(self, recipient_email: str, quote_data: Dict, items_df: pd.DataFrame, 
                        client_data: Dict, additional_message: str = "", 
                        attach_pdf: bool = True, attach_excel: bool = False) -> Tuple[bool, str]:
        """Send quote email (backward compatibility - no CC)"""
        return self.send_quote_email_with_cc(
            recipient_email=recipient_email,
            quote_data=quote_data,
            items_df=items_df,
            client_data=client_data,
            cc_email=None,
            additional_message=additional_message,
            attach_pdf=attach_pdf,
            attach_excel=attach_excel
        )
    
    def _create_email_body(self, quote_data: Dict, items_df: pd.DataFrame, 
                          client_data: Dict, additional_message: str = "") -> str:
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
            line_total = unit_price * quantity
            
            items_html += f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 8px; text-align: left;">{sku}</td>
                <td style="padding: 8px; text-align: left;">{description}</td>
                <td style="padding: 8px; text-align: center;">{quantity}</td>
                <td style="padding: 8px; text-align: right;">${unit_price:,.2f}</td>
                <td style="padding: 8px; text-align: right; font-weight: bold;">${line_total:,.2f}</td>
            </tr>
            """
        
        # Additional message section
        additional_html = ""
        if additional_message.strip():
            additional_html = f"""
            <div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #20429C;">
                <h3 style="margin-top: 0; color: #20429C;">Additional Message:</h3>
                <p style="margin-bottom: 0; white-space: pre-wrap;">{additional_message}</p>
            </div>
            """
        
        # Complete HTML email body
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
                .totals {{ background-color: #f8f9fa; padding: 15px; margin: 20px 0; }}
                .total-row {{ font-weight: bold; font-size: 1.1em; }}
                .footer {{ background-color: #f1f1f1; padding: 20px; text-align: center; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>TURBO AIR EQUIPMENT</h1>
                <h2>Equipment Quote</h2>
            </div>
            
            <div class="content">
                <div class="quote-info">
                    <h3>Quote Information</h3>
                    <p><strong>Quote Number:</strong> {quote_data.get('quote_number', 'N/A')}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                    <p><strong>Client:</strong> {client_data.get('company', 'N/A')}</p>
                    <p><strong>Contact:</strong> {client_data.get('contact_name', 'N/A')}</p>
                </div>
                
                {additional_html}
                
                <h3>Equipment List</h3>
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
                    <table style="width: 100%; margin: 0;">
                        <tr>
                            <td style="text-align: right; padding: 5px;"><strong>Subtotal:</strong></td>
                            <td style="text-align: right; padding: 5px; width: 120px;"><strong>${subtotal:,.2f}</strong></td>
                        </tr>
                        <tr>
                            <td style="text-align: right; padding: 5px;"><strong>Tax ({tax_rate_display:.1f}%):</strong></td>
                            <td style="text-align: right; padding: 5px;"><strong>${tax_amount:,.2f}</strong></td>
                        </tr>
                        <tr class="total-row" style="border-top: 2px solid #20429C;">
                            <td style="text-align: right; padding: 10px 5px 5px 5px;"><strong>TOTAL:</strong></td>
                            <td style="text-align: right; padding: 10px 5px 5px 5px; font-size: 1.2em;"><strong>${total:,.2f}</strong></td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <div class="footer">
                <p><strong>Thank you for choosing Turbo Air Equipment!</strong></p>
                <p>This quote is valid for 30 days from the date of issue.</p>
                <p>For questions about this quote, please contact us at {self.sender_email}</p>
            </div>
        </body>
        </html>
        """
        
        return html_body

# Global email service instance
_email_service = None

def get_email_service() -> EmailService:
    """Get global email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

def test_email_connection() -> Tuple[bool, str]:
    """Test email connection - wrapper function"""
    try:
        email_service = get_email_service()
        return email_service.test_connection()
    except Exception as e:
        return False, f"Test connection error: {str(e)}"

def show_email_quote_dialog(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict):
    """Show email quote dialog with CC support, improved UI and error handling"""
    
    st.markdown("### Send Quote via Email")
    
    # Show email configuration status
    email_service = get_email_service()
    if email_service.configured:
        st.success(f"✅ Email configured: {email_service.sender_email}")
        st.info(f"🌐 SMTP: {email_service.smtp_server}:{email_service.smtp_port}")
    else:
        st.error("❌ Email not configured")
        return
    
    # Email form with CC support
    with st.form("email_quote_form"):
        # Recipient email
        recipient_email = st.text_input(
            "📧 To (Recipient Email):",
            value=client_data.get('contact_email', ''),
            placeholder="Enter recipient email address"
        )
        
        # CC email - NEW FEATURE
        cc_email = st.text_input(
            "📋 CC (Optional):",
            value="andres@turboairmexico.com",  # Default CC
            placeholder="Enter CC email address (optional)"
        )
        
        # Additional message
        additional_message = st.text_area(
            "💬 Additional Message (optional):",
            placeholder="Add any additional notes or message...",
            height=100
        )
        
        # Attachment options
        st.markdown("**📎 Attachments:**")
        col1, col2 = st.columns(2)
        with col1:
            attach_pdf = st.checkbox("📄 Attach PDF", value=True)
        with col2:
            attach_excel = st.checkbox("📊 Attach Excel", value=False)
        
        # Send button
        send_submitted = st.form_submit_button("📧 Send Email", use_container_width=True, type="primary")
        
        if send_submitted:
            if not recipient_email:
                st.error("Please enter a recipient email address")
            elif not recipient_email.count('@') == 1 or not '.' in recipient_email.split('@')[1]:
                st.error("Please enter a valid email address")
            else:
                # Validate CC email if provided
                cc_valid = True
                if cc_email.strip():
                    if not cc_email.count('@') == 1 or not '.' in cc_email.split('@')[1]:
                        st.error("Please enter a valid CC email address")
                        cc_valid = False
                
                if cc_valid:
                    with st.spinner(f"Sending quote to {recipient_email}..."):
                        try:
                            success, message = email_service.send_quote_email_with_cc(
                                recipient_email=recipient_email,
                                cc_email=cc_email.strip() if cc_email.strip() else None,
                                quote_data=quote_data,
                                items_df=items_df,
                                client_data=client_data,
                                additional_message=additional_message,
                                attach_pdf=attach_pdf,
                                attach_excel=attach_excel
                            )
                            
                            if success:
                                st.success(f"✅ {message}")
                                if cc_email.strip():
                                    st.info(f"📋 CC sent to: {cc_email}")
                                st.balloons()
                            else:
                                st.error(f"❌ {message}")
                                
                        except Exception as e:
                            st.error(f"❌ Failed to send email: {str(e)}")
    
    # Cancel button outside form
    if st.button("Cancel", key="cancel_email"):
        st.rerun()