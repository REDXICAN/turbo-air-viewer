"""
Email functionality for Turbo Air Equipment Viewer
Complete version with PDF/Excel attachments, CC support, file size reporting, and working email form
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
    
    def _create_professional_email_body(self, quote_data: Dict, items_df: pd.DataFrame, 
                                       client_data: Dict, additional_message: str = "") -> str:
        """Create professional HTML email body with full template"""
        
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
        
        # Complete professional HTML email body
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

def send_email_with_attachments(email_service, recipient_email: str, quote_data: Dict, 
                               items_df: pd.DataFrame, client_data: Dict,
                               cc_email: str = None, additional_message: str = "",
                               attach_pdf: bool = False, attach_excel: bool = False) -> Tuple[bool, str]:
    """Send email with professional template and robust attachment handling"""
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.application import MIMEApplication
        
        st.write("🔄 Creating professional email message...")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_service.sender_email
        msg['To'] = recipient_email
        if cc_email:
            msg['Cc'] = cc_email
        msg['Subject'] = f"Quote {quote_data.get('quote_number', 'N/A')} - Turbo Air Equipment"
        
        # Create professional email body using the EmailService method
        st.write("🔄 Creating professional HTML email body...")
        body = email_service._create_professional_email_body(quote_data, items_df, client_data, additional_message)
        msg.attach(MIMEText(body, 'html'))
        st.write("✅ Professional email body created")
        
        attachment_details = []
        
        # Handle PDF attachment with file size reporting
        if attach_pdf:
            try:
                st.write("📄 Generating PDF attachment...")
                from .export import generate_pdf_quote
                pdf_buffer = generate_pdf_quote(quote_data, items_df, client_data)
                
                if pdf_buffer and len(pdf_buffer.getvalue()) > 0:
                    file_size = len(pdf_buffer.getvalue())
                    
                    # Create attachment
                    pdf_attachment = MIMEApplication(pdf_buffer.getvalue(), _subtype='pdf')
                    pdf_attachment.add_header(
                        'Content-Disposition', 
                        'attachment', 
                        filename=f"Quote_{quote_data.get('quote_number', 'N/A')}.pdf"
                    )
                    msg.attach(pdf_attachment)
                    
                    attachment_details.append(f"PDF ({file_size:,} bytes)")
                    st.write(f"✅ PDF attached successfully ({file_size:,} bytes)")
                else:
                    st.error("❌ PDF buffer is empty")
                    attach_pdf = False
                    
            except Exception as pdf_error:
                st.error(f"❌ PDF attachment error: {str(pdf_error)}")
                attach_pdf = False
        
        # Handle Excel attachment with file size reporting
        if attach_excel:
            try:
                st.write("📊 Generating Excel attachment...")
                from .export import generate_excel_quote
                excel_buffer = generate_excel_quote(quote_data, items_df, client_data)
                
                if excel_buffer and len(excel_buffer.getvalue()) > 0:
                    file_size = len(excel_buffer.getvalue())
                    
                    # Create attachment
                    excel_attachment = MIMEApplication(
                        excel_buffer.getvalue(), 
                        _subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                    excel_attachment.add_header(
                        'Content-Disposition', 
                        'attachment', 
                        filename=f"Quote_{quote_data.get('quote_number', 'N/A')}.xlsx"
                    )
                    msg.attach(excel_attachment)
                    
                    attachment_details.append(f"Excel ({file_size:,} bytes)")
                    st.write(f"✅ Excel attached successfully ({file_size:,} bytes)")
                else:
                    st.error("❌ Excel buffer is empty")
                    attach_excel = False
                    
            except Exception as excel_error:
                st.error(f"❌ Excel attachment error: {str(excel_error)}")
                attach_excel = False
        
        # Send email
        st.write("🔄 Sending email via SMTP...")
        server = smtplib.SMTP(email_service.smtp_server, email_service.smtp_port)
        server.starttls()
        server.login(email_service.sender_email, email_service.sender_password)
        
        # Prepare recipients
        recipients = [recipient_email]
        if cc_email:
            recipients.append(cc_email)
        
        # Send message
        server.sendmail(email_service.sender_email, recipients, msg.as_string())
        server.quit()
        
        # Create detailed success message
        success_msg = f"Email sent successfully to {recipient_email}"
        if cc_email:
            success_msg += f" (CC: {cc_email})"
        
        if attachment_details:
            success_msg += f" with attachments: {', '.join(attachment_details)}"
        
        return True, success_msg
        
    except Exception as e:
        return False, f"Email sending failed: {str(e)}"

def show_email_quote_form(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict):
    """Show email quote form directly - always visible"""
    
    st.markdown("### Send Quote via Email")
    
    # Show email configuration status
    email_service = get_email_service()
    if not email_service.configured:
        st.error("❌ Email not configured")
        return
    
    st.success(f"✅ Email configured: {email_service.sender_email}")
    st.info(f"🌐 SMTP: {email_service.smtp_server}:{email_service.smtp_port}")
    
    # EMAIL FORM - ALWAYS DISPLAYED
    st.markdown("**📧 Email Details:**")
    
    # Recipient email
    recipient_email = st.text_input(
        "📧 To (Recipient):",
        value=client_data.get('contact_email', ''),
        placeholder="Enter recipient email address",
        key="email_recipient"
    )
    
    # CC email - EMPTY BY DEFAULT
    cc_email = st.text_input(
        "📋 CC (Optional):",
        value="",
        placeholder="Enter CC email address (optional)",
        key="email_cc"
    )
    
    # Additional message
    additional_message = st.text_area(
        "💬 Additional Message (optional):",
        placeholder="Add any additional notes or message...",
        height=100,
        key="email_message"
    )
    
    # Attachment options
    st.markdown("**📎 Attachments:**")
    col1, col2 = st.columns(2)
    with col1:
        attach_pdf = st.checkbox("📄 Attach PDF Quote", value=True, key="attach_pdf_check")
    with col2:
        attach_excel = st.checkbox("📊 Attach Excel Quote", value=False, key="attach_excel_check")
    
    # Send Email Button
    if st.button("📧 Send Professional Quote Email", use_container_width=True, type="primary", key="send_email_btn"):
        # Basic validation
        if not recipient_email or '@' not in recipient_email:
            st.error("Please enter a valid recipient email address")
        elif cc_email.strip() and '@' not in cc_email:
            st.error("Please enter a valid CC email address")
        else:
            st.write("✅ Starting email send process...")
            
            # Send email with full debugging and file size reporting
            with st.spinner("Sending professional quote email..."):
                try:
                    success, message = send_email_with_attachments(
                        email_service=email_service,
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
                            st.info(f"📋 CC sent to: {cc_email.strip()}")
                        st.balloons()
                    else:
                        st.error(f"❌ {message}")
                        
                except Exception as e:
                    st.error(f"❌ Email sending failed: {str(e)}")
                    st.exception(e)
    
    # Export buttons below the email form
    st.markdown("---")
    st.markdown("### Export Options")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Export PDF", use_container_width=True, key="export_pdf_btn"):
            try:
                from .export import generate_pdf_quote
                pdf_buffer = generate_pdf_quote(quote_data, items_df, client_data)
                
                if pdf_buffer:
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_buffer.getvalue(),
                        file_name=f"Quote_{quote_data.get('quote_number', 'N/A')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.error("Failed to generate PDF")
            except Exception as e:
                st.error(f"PDF generation error: {str(e)}")
    
    with col2:
        if st.button("📊 Export Excel", use_container_width=True, key="export_excel_btn"):
            try:
                from .export import generate_excel_quote
                excel_buffer = generate_excel_quote(quote_data, items_df, client_data)
                
                if excel_buffer:
                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_buffer.getvalue(),
                        file_name=f"Quote_{quote_data.get('quote_number', 'N/A')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.error("Failed to generate Excel")
            except Exception as e:
                st.error(f"Excel generation error: {str(e)}")