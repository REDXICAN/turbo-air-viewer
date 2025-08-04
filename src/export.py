"""
Export functionality for Turbo Air Equipment Viewer
Handles CSV and PDF exports
"""

import io
import csv
from datetime import datetime
import pandas as pd
from typing import Dict, List, Optional
import requests
from PIL import Image

# Logo URL from GitHub repository
LOGO_URL = "https://raw.githubusercontent.com/REDXICAN/turbo-air-viewer/main/turbo_air_logo.png"

def download_logo():
    """Download and return logo image"""
    try:
        response = requests.get(LOGO_URL)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except Exception as e:
        print(f"Could not download logo: {e}")
    return None

def export_quote_to_csv(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict) -> io.BytesIO:
    """Export quote to CSV format including all details and tax"""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    # Write header information
    writer.writerow(['TURBO AIR EQUIPMENT QUOTE'])
    writer.writerow([])
    
    # Quote Information
    writer.writerow(['Quote Information'])
    writer.writerow(['Quote Number:', quote_data.get('quote_number', 'N/A')])
    writer.writerow(['Date:', datetime.now().strftime('%B %d, %Y')])
    writer.writerow(['Client:', client_data.get('company', 'N/A')])
    writer.writerow(['Contact:', client_data.get('contact_name', 'N/A')])
    writer.writerow(['Email:', client_data.get('contact_email', 'N/A')])
    writer.writerow([])
    
    # Equipment List
    writer.writerow(['Equipment List'])
    writer.writerow(['SKU', 'Description', 'Quantity', 'Unit Price', 'Total'])
    
    # Items
    for idx, item in items_df.iterrows():
        sku = str(item.get('sku', 'Unknown'))
        description = str(item.get('product_type', ''))
        quantity = int(item.get('quantity', 1))
        unit_price = float(item.get('price', 0))
        total_price = unit_price * quantity
        
        writer.writerow([sku, description, quantity, f"${unit_price:,.2f}", f"${total_price:,.2f}"])
    
    writer.writerow([])
    
    # Totals with Tax
    subtotal = float(quote_data.get('subtotal', 0))
    tax_rate = float(quote_data.get('tax_rate', 0))
    if tax_rate > 1:
        tax_rate_display = tax_rate
    else:
        tax_rate_display = tax_rate * 100
    tax_amount = float(quote_data.get('tax_amount', 0))
    total = float(quote_data.get('total_amount', 0))
    
    writer.writerow(['', '', '', 'Subtotal:', f"${subtotal:,.2f}"])
    writer.writerow(['', '', '', f'Tax ({tax_rate_display:.1f}%):', f"${tax_amount:,.2f}"])
    writer.writerow(['', '', '', 'TOTAL:', f"${total:,.2f}"])
    
    # Convert to bytes
    byte_buffer = io.BytesIO()
    byte_buffer.write(buffer.getvalue().encode('utf-8'))
    byte_buffer.seek(0)
    
    return byte_buffer

def export_quote_to_pdf(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict) -> io.BytesIO:
    """Export quote to PDF format with Turbo Air logo"""
    buffer = io.BytesIO()
    
    # Create a simple text-based PDF content
    content = f"""TURBO AIR EQUIPMENT QUOTE

Quote Information:
Quote Number: {quote_data.get('quote_number', 'N/A')}
Date: {datetime.now().strftime('%B %d, %Y')}
Client: {client_data.get('company', 'N/A')}
Contact: {client_data.get('contact_name', 'N/A')}
Email: {client_data.get('contact_email', 'N/A')}

Equipment List:
"""
    
    # Add items
    for idx, item in items_df.iterrows():
        sku = str(item.get('sku', 'Unknown'))
        description = str(item.get('product_type', ''))
        quantity = int(item.get('quantity', 1))
        unit_price = float(item.get('price', 0))
        total_price = unit_price * quantity
        content += f"\n{sku} - {description} - Qty: {quantity} - ${unit_price:,.2f} - Total: ${total_price:,.2f}"
    
    # Add totals
    subtotal = float(quote_data.get('subtotal', 0))
    tax_rate = float(quote_data.get('tax_rate', 0))
    if tax_rate > 1:
        tax_rate_display = tax_rate
    else:
        tax_rate_display = tax_rate * 100
    tax_amount = float(quote_data.get('tax_amount', 0))
    total = float(quote_data.get('total_amount', 0))
    
    content += f"""

Financial Summary:
Subtotal: ${subtotal:,.2f}
Tax ({tax_rate_display:.1f}%): ${tax_amount:,.2f}
TOTAL: ${total:,.2f}

Thank you for choosing Turbo Air Equipment!
This quote is valid for 30 days from the date of issue.
"""
    
    # Try to use reportlab if available
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Add logo (image only)
        try:
            logo_img = download_logo()
            if logo_img:
                # Save logo to temporary buffer
                logo_buffer = io.BytesIO()
                logo_img.save(logo_buffer, format='PNG')
                logo_buffer.seek(0)
                
                # Create reportlab image
                logo = RLImage(logo_buffer, width=3*inch, height=1*inch)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 20))
        except Exception as e:
            # Just add spacing if logo fails - no text fallback
            story.append(Spacer(1, 20))
        
        # Quote Information
        quote_info_data = [
            ['Quote Number:', str(quote_data.get('quote_number', 'N/A'))],
            ['Date:', datetime.now().strftime('%B %d, %Y')],
            ['Client:', str(client_data.get('company', 'N/A'))],
            ['Contact:', str(client_data.get('contact_name', 'N/A'))],
            ['Email:', str(client_data.get('contact_email', 'N/A'))]
        ]
        
        quote_table = Table(quote_info_data, colWidths=[2*inch, 4*inch])
        quote_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F2F2F7'))
        ]))
        
        story.append(quote_table)
        story.append(Spacer(1, 20))
        
        # Equipment List
        items_data = [['SKU', 'Description', 'Qty', 'Unit Price', 'Total']]
        
        for idx, item in items_df.iterrows():
            sku = str(item.get('sku', 'Unknown'))
            description = str(item.get('product_type', ''))[:50]
            quantity = str(int(item.get('quantity', 1)))
            unit_price = f"${float(item.get('price', 0)):,.2f}"
            total_price = f"${float(item.get('price', 0)) * int(item.get('quantity', 1)):,.2f}"
            
            items_data.append([sku, description, quantity, unit_price, total_price])
        
        items_table = Table(items_data, colWidths=[1.5*inch, 3*inch, 0.7*inch, 1.2*inch, 1.2*inch])
        items_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#20429C')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Totals
        totals_data = [
            ['Subtotal:', f"${subtotal:,.2f}"],
            [f'Tax ({tax_rate_display:.1f}%):', f"${tax_amount:,.2f}"],
            ['TOTAL:', f"${total:,.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[5.5*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 1), 10),
            ('FONTSIZE', (0, 2), (-1, 2), 12),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('LINEBELOW', (0, 1), (-1, 1), 1, colors.black),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#20429C')),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.whitesmoke)
        ]))
        
        story.append(totals_table)
        
        # Build PDF
        doc.build(story)
        
    except ImportError:
        # Fallback to simple text if reportlab not available
        buffer.write(content.encode('utf-8'))
    
    buffer.seek(0)
    return buffer

def generate_pdf_quote(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict) -> io.BytesIO:
    """Generate PDF quote - alias for export_quote_to_pdf"""
    return export_quote_to_pdf(quote_data, items_df, client_data)