"""
Fixed Export functionality for Turbo Air Equipment Viewer
Improved PDF generation with better image handling
"""

import io
import os
import base64
from datetime import datetime
from typing import Dict, List
import pandas as pd

# Excel exports
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.drawing import Image as XLImage
    from openpyxl.utils.dataframe import dataframe_to_rows
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

# PDF exports  
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image as PILImage
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

def get_product_image_path(sku: str) -> str:
    """Get the path to product image with better path handling"""
    possible_paths = [
        f"pdf_screenshots/{sku}/{sku} P.1.png",
        f"pdf_screenshots/{sku}/{sku}_P.1.png", 
        f"pdf_screenshots/{sku}/{sku}.png",
        f"pdf_screenshots/{sku}/page_1.png",
        f"pdf_screenshots/{sku.upper()}/{sku.upper()} P.1.png",
        f"pdf_screenshots/{sku.upper()}/{sku.upper()}_P.1.png",
        f"pdf_screenshots/{sku.upper()}/{sku.upper()}.png",
        f"pdf_screenshots/{sku.lower()}/{sku.lower()} P.1.png",
        f"pdf_screenshots/{sku.lower()}/{sku.lower()}_P.1.png",
        f"pdf_screenshots/{sku.lower()}/{sku.lower()}.png"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def resize_image_for_pdf(image_path: str, max_width: float = 0.8, max_height: float = 0.6) -> io.BytesIO:
    """Resize image for PDF inclusion"""
    try:
        from PIL import Image as PILImage
        
        # Open and convert image
        with PILImage.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Calculate new size maintaining aspect ratio
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height
            
            # Convert inches to pixels (assuming 72 DPI)
            max_width_px = int(max_width * inch * 72 / 72)
            max_height_px = int(max_height * inch * 72 / 72)
            
            if img_width > max_width_px or img_height > max_height_px:
                if aspect_ratio > 1:  # Wider than tall
                    new_width = max_width_px
                    new_height = int(max_width_px / aspect_ratio)
                else:  # Taller than wide
                    new_height = max_height_px
                    new_width = int(max_height_px * aspect_ratio)
                
                img = img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
            
            # Save to BytesIO
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            return buffer
    except Exception as e:
        print(f"Error resizing image {image_path}: {e}")
        return None

def generate_excel_quote(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict) -> io.BytesIO:
    """Generate Excel quote with enhanced formatting and images"""
    if not EXCEL_AVAILABLE:
        raise ImportError("openpyxl not available for Excel export")
    
    buffer = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Quote"
    
    # Styles
    header_font = Font(name='Arial', size=16, bold=True, color='FFFFFF')
    subheader_font = Font(name='Arial', size=12, bold=True)
    normal_font = Font(name='Arial', size=10)
    
    header_fill = PatternFill(start_color='20429C', end_color='20429C', fill_type='solid')
    light_fill = PatternFill(start_color='F2F2F7', end_color='F2F2F7', fill_type='solid')
    
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'), 
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Header
    ws.merge_cells('A1:F1')
    ws['A1'] = 'TURBO AIR - EQUIPMENT QUOTE'
    ws['A1'].font = header_font
    ws['A1'].fill = header_fill
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 30
    
    # Quote info
    current_row = 3
    ws[f'A{current_row}'] = 'Quote Information'
    ws[f'A{current_row}'].font = subheader_font
    current_row += 1
    
    quote_info = [
        ['Quote Number:', quote_data.get('quote_number', 'N/A')],
        ['Date:', datetime.now().strftime('%B %d, %Y')],
        ['Client:', client_data.get('company', 'N/A')],
        ['Contact:', client_data.get('contact_name', 'N/A')],
        ['Email:', client_data.get('contact_email', 'N/A')]
    ]
    
    for info in quote_info:
        ws[f'A{current_row}'] = info[0]
        ws[f'B{current_row}'] = info[1]
        ws[f'A{current_row}'].font = Font(bold=True)
        current_row += 1
    
    current_row += 2
    
    # Items header
    ws[f'A{current_row}'] = 'Equipment List'
    ws[f'A{current_row}'].font = subheader_font
    current_row += 1
    
    # Table headers
    headers = ['Image', 'SKU', 'Description', 'Qty', 'Unit Price', 'Total']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=current_row, column=col, value=header)
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    
    # Set column widths
    ws.column_dimensions['A'].width = 15  # Image column
    ws.column_dimensions['B'].width = 20  # SKU
    ws.column_dimensions['C'].width = 40  # Description  
    ws.column_dimensions['D'].width = 8   # Qty
    ws.column_dimensions['E'].width = 12  # Unit Price
    ws.column_dimensions['F'].width = 12  # Total
    
    current_row += 1
    
    # Add items with images
    for idx, item in items_df.iterrows():
        sku = item.get('sku', 'Unknown')
        description = item.get('product_type', '')
        quantity = item.get('quantity', 1)
        unit_price = item.get('price', 0)
        total_price = unit_price * quantity
        
        # Try to add product image
        image_path = get_product_image_path(sku)
        if image_path:
            try:
                img = XLImage(image_path)
                img.width = 80
                img.height = 60
                ws.add_image(img, f'A{current_row}')
                ws.row_dimensions[current_row].height = 50
            except Exception as e:
                print(f"Could not add image for {sku}: {e}")
                ws[f'A{current_row}'] = '📷'
        else:
            ws[f'A{current_row}'] = '📷'
        
        # Add item data
        ws[f'B{current_row}'] = sku
        ws[f'C{current_row}'] = description
        ws[f'D{current_row}'] = quantity
        ws[f'E{current_row}'] = f"${unit_price:,.2f}"
        ws[f'F{current_row}'] = f"${total_price:,.2f}"
        
        # Format cells
        for col in range(1, 7):
            cell = ws.cell(row=current_row, column=col)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        current_row += 1
    
    # Totals
    current_row += 1
    subtotal = quote_data.get('subtotal', 0)
    tax_rate = quote_data.get('tax_rate', 0)
    tax_amount = quote_data.get('tax_amount', 0)
    total = quote_data.get('total_amount', 0)
    
    ws[f'E{current_row}'] = 'Subtotal:'
    ws[f'F{current_row}'] = f"${subtotal:,.2f}"
    ws[f'E{current_row}'].font = Font(bold=True)
    current_row += 1
    
    ws[f'E{current_row}'] = f'Tax ({tax_rate:.1f}%):'
    ws[f'F{current_row}'] = f"${tax_amount:,.2f}"
    ws[f'E{current_row}'].font = Font(bold=True)
    current_row += 1
    
    ws[f'E{current_row}'] = 'TOTAL:'
    ws[f'F{current_row}'] = f"${total:,.2f}"
    ws[f'E{current_row}'].font = Font(bold=True, size=14)
    ws[f'F{current_row}'].font = Font(bold=True, size=14)
    
    wb.save(buffer)
    buffer.seek(0)
    return buffer

def generate_pdf_quote(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict) -> io.BytesIO:
    """Generate PDF quote with enhanced formatting and product images"""
    if not PDF_AVAILABLE:
        raise ImportError("reportlab not available for PDF export")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#20429C'),
        spaceAfter=20,
        alignment=1  # Center
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'], 
        fontSize=14,
        textColor=colors.HexColor('#20429C'),
        spaceAfter=10
    )
    
    story = []
    
    # Title
    story.append(Paragraph("TURBO AIR - EQUIPMENT QUOTE", title_style))
    story.append(Spacer(1, 20))
    
    # Quote information table
    quote_info_data = [
        ['Quote Number:', quote_data.get('quote_number', 'N/A')],
        ['Date:', datetime.now().strftime('%B %d, %Y')],
        ['Client:', client_data.get('company', 'N/A')],
        ['Contact:', client_data.get('contact_name', 'N/A')],
        ['Email:', client_data.get('contact_email', 'N/A')]
    ]
    
    quote_table = Table(quote_info_data, colWidths=[2*inch, 3*inch])
    quote_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F2F2F7'))
    ]))
    
    story.append(quote_table)
    story.append(Spacer(1, 20))
    
    # Equipment list header
    story.append(Paragraph("Equipment List", header_style))
    
    # Prepare items data with improved image handling
    items_data = [['Image', 'SKU', 'Description', 'Qty', 'Unit Price', 'Total']]
    
    for idx, item in items_df.iterrows():
        sku = item.get('sku', 'Unknown')
        description = item.get('product_type', '')[:40]  # Truncate long descriptions
        quantity = item.get('quantity', 1)
        unit_price = item.get('price', 0)
        total_price = unit_price * quantity
        
        # Try to add product image with better error handling
        image_cell = "📷"  # Default placeholder
        
        image_path = get_product_image_path(sku)
        if image_path:
            try:
                # Resize image for PDF
                resized_buffer = resize_image_for_pdf(image_path, 0.8, 0.6)
                if resized_buffer:
                    img = RLImage(resized_buffer, width=0.8*inch, height=0.6*inch)
                    image_cell = img
                else:
                    # Try original image with smaller size
                    img = RLImage(image_path, width=0.6*inch, height=0.45*inch)
                    image_cell = img
            except Exception as e:
                print(f"Could not add image for {sku}: {e}")
                image_cell = "📷"
        
        items_data.append([
            image_cell,
            sku,
            description,
            str(quantity),
            f"${unit_price:,.2f}",
            f"${total_price:,.2f}"
        ])
    
    # Create items table with better styling
    items_table = Table(items_data, colWidths=[1*inch, 1.2*inch, 2.5*inch, 0.5*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#20429C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('LEADING', (0, 0), (-1, -1), 12)  # Line spacing
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 20))
    
    # Totals
    subtotal = quote_data.get('subtotal', 0)
    tax_rate = quote_data.get('tax_rate', 0)
    tax_amount = quote_data.get('tax_amount', 0)
    total = quote_data.get('total_amount', 0)
    
    totals_data = [
        ['Subtotal:', f"${subtotal:,.2f}"],
        [f'Tax ({tax_rate:.1f}%):', f"${tax_amount:,.2f}"],
        ['TOTAL:', f"${total:,.2f}"]
    ]
    
    totals_table = Table(totals_data, colWidths=[4*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 1), 10),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 1), (-1, 1), 1, colors.black),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#20429C')),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.whitesmoke)
    ]))
    
    story.append(totals_table)
    
    # Footer
    story.append(Spacer(1, 30))
    footer_text = """
    <para align="center" fontSize="9" textColor="#666666">
    Thank you for choosing Turbo Air Equipment!<br/>
    This quote is valid for 30 days from the date of issue.<br/>
    For questions, please contact us at turboairquotes@gmail.com
    </para>
    """
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF with error handling
    try:
        doc.build(story)
    except Exception as e:
        print(f"Error building PDF: {e}")
        # Create a simple text-only version if image processing fails
        story_simple = [item for item in story if not isinstance(item, Table) or 'Image' not in str(item)]
        doc.build(story_simple)
    
    buffer.seek(0)
    return buffer

def prepare_email_attachments(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict) -> Dict[str, io.BytesIO]:
    """Prepare email attachments (Excel and PDF) with better error handling"""
    attachments = {}
    
    try:
        # Generate Excel attachment
        if EXCEL_AVAILABLE:
            excel_buffer = generate_excel_quote(quote_data, items_df, client_data)
            attachments[f"Quote_{quote_data['quote_number']}.xlsx"] = excel_buffer
        else:
            print("Excel export not available - openpyxl not installed")
        
        # Generate PDF attachment
        if PDF_AVAILABLE:
            pdf_buffer = generate_pdf_quote(quote_data, items_df, client_data)
            attachments[f"Quote_{quote_data['quote_number']}.pdf"] = pdf_buffer
        else:
            print("PDF export not available - reportlab not installed")
        
    except Exception as e:
        print(f"Error preparing attachments: {e}")
        # Return any successfully created attachments
    
    return attachments