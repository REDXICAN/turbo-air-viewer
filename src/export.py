"""
Export functionality for Turbo Air Equipment Viewer
Handles PDF and Excel exports
"""

import io
from datetime import datetime
import pandas as pd
from typing import Dict
import requests
from PIL import Image

# Logo URL from GitHub repository
LOGO_URL = "https://raw.githubusercontent.com/REDXICAN/turbo-air-viewer/master/Turboair_Logo_01.png"

def download_logo():
    """Download and return logo image"""
    try:
        response = requests.get(LOGO_URL)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except Exception as e:
        print(f"Could not download logo: {e}")
    return None

def export_quote_to_pdf(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict) -> io.BytesIO:
    """Export quote to PDF format with Turbo Air logo"""
    buffer = io.BytesIO()
    
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
        
        # Add logo at top center
        try:
            logo_img = download_logo()
            if logo_img:
                # Save logo to temporary buffer
                logo_buffer = io.BytesIO()
                logo_img.save(logo_buffer, format='PNG')
                logo_buffer.seek(0)
                
                # Create reportlab image - centered at top
                logo = RLImage(logo_buffer, width=4*inch, height=1.5*inch)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 20))
        except Exception as e:
            # Fallback to text if logo fails
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#20429C'),
                spaceAfter=20,
                alignment=1
            )
            story.append(Paragraph("TURBO AIR EQUIPMENT", title_style))
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
        subtotal = float(quote_data.get('subtotal', 0))
        tax_rate = float(quote_data.get('tax_rate', 0))
        if tax_rate > 1:
            tax_rate_display = tax_rate
        else:
            tax_rate_display = tax_rate * 100
        tax_amount = float(quote_data.get('tax_amount', 0))
        total = float(quote_data.get('total_amount', 0))
        
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
        story.append(Spacer(1, 20))
        
        # Footer
        footer_text = """
        Thank you for choosing Turbo Air Equipment!
        This quote is valid for 30 days from the date of issue.
        """
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=1
        )
        story.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(story)
        
    except ImportError:
        # Fallback to simple text if reportlab not available
        content = f"""TURBO AIR EQUIPMENT

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
        
        buffer.write(content.encode('utf-8'))
    
    buffer.seek(0)
    return buffer

def export_quote_to_excel(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict) -> io.BytesIO:
    """Export quote to Excel format with Turbo Air logo"""
    buffer = io.BytesIO()
    
    try:
        # Try to use openpyxl if available
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.drawing.image import Image as ExcelImage
        
        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Quote"
        
        # Styles
        title_font = Font(name='Arial', size=16, bold=True, color='20429C')
        header_font = Font(name='Arial', size=12, bold=True)
        regular_font = Font(name='Arial', size=10)
        
        # Try to add logo at top center
        try:
            logo_img = download_logo()
            if logo_img:
                # Save logo to temporary file
                logo_buffer = io.BytesIO()
                logo_img.save(logo_buffer, format='PNG')
                logo_buffer.seek(0)
                
                # Add logo to Excel
                img = ExcelImage(logo_buffer)
                img.width = 300  # Adjust width as needed
                img.height = 100  # Adjust height as needed
                ws.add_image(img, 'B1')  # Center in columns B-D
                
                # Start content after logo
                start_row = 8
            else:
                # Fallback to text title
                ws['A1'] = 'TURBO AIR EQUIPMENT'
                ws['A1'].font = title_font
                ws.merge_cells('A1:E1')
                ws['A1'].alignment = Alignment(horizontal='center')
                start_row = 3
        except Exception as e:
            # Fallback to text title
            ws['A1'] = 'TURBO AIR EQUIPMENT'
            ws['A1'].font = title_font
            ws.merge_cells('A1:E1')
            ws['A1'].alignment = Alignment(horizontal='center')
            start_row = 3
        
        # Quote Information
        row = start_row
        ws[f'A{row}'] = 'Quote Information:'
        ws[f'A{row}'].font = header_font
        
        row += 1
        info_data = [
            ['Quote Number:', quote_data.get('quote_number', 'N/A')],
            ['Date:', datetime.now().strftime('%B %d, %Y')],
            ['Client:', client_data.get('company', 'N/A')],
            ['Contact:', client_data.get('contact_name', 'N/A')],
            ['Email:', client_data.get('contact_email', 'N/A')]
        ]
        
        for info in info_data:
            ws[f'A{row}'] = info[0]
            ws[f'A{row}'].font = Font(name='Arial', size=10, bold=True)
            ws[f'B{row}'] = info[1]
            ws[f'B{row}'].font = regular_font
            row += 1
        
        # Equipment List
        row += 2
        ws[f'A{row}'] = 'Equipment List:'
        ws[f'A{row}'].font = header_font
        
        row += 1
        headers = ['SKU', 'Description', 'Quantity', 'Unit Price', 'Total']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = PatternFill(start_color='20429C', end_color='20429C', fill_type='solid')
            cell.font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
        
        # Items
        for idx, item in items_df.iterrows():
            row += 1
            sku = str(item.get('sku', 'Unknown'))
            description = str(item.get('product_type', ''))
            quantity = int(item.get('quantity', 1))
            unit_price = float(item.get('price', 0))
            total_price = unit_price * quantity
            
            ws[f'A{row}'] = sku
            ws[f'B{row}'] = description
            ws[f'C{row}'] = quantity
            ws[f'D{row}'] = unit_price
            ws[f'E{row}'] = total_price
            
            for col in range(1, 6):
                ws.cell(row=row, column=col).font = regular_font
        
        # Totals
        row += 2
        subtotal = float(quote_data.get('subtotal', 0))
        tax_rate = float(quote_data.get('tax_rate', 0))
        if tax_rate > 1:
            tax_rate_display = tax_rate
        else:
            tax_rate_display = tax_rate * 100
        tax_amount = float(quote_data.get('tax_amount', 0))
        total = float(quote_data.get('total_amount', 0))
        
        ws[f'D{row}'] = 'Subtotal:'
        ws[f'D{row}'].font = header_font
        ws[f'E{row}'] = subtotal
        
        row += 1
        ws[f'D{row}'] = f'Tax ({tax_rate_display:.1f}%):'
        ws[f'D{row}'].font = header_font
        ws[f'E{row}'] = tax_amount
        
        row += 1
        ws[f'D{row}'] = 'TOTAL:'
        ws[f'D{row}'].font = Font(name='Arial', size=12, bold=True)
        ws[f'E{row}'] = total
        ws[f'E{row}'].font = Font(name='Arial', size=12, bold=True)
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        
        # Save to buffer
        wb.save(buffer)
        
    except ImportError:
        # Fallback to pandas Excel if openpyxl not available
        import pandas as pd
        
        # Create DataFrame for export
        export_data = []
        export_data.append(['TURBO AIR EQUIPMENT', '', '', '', ''])
        export_data.append(['', '', '', '', ''])
        export_data.append(['Quote Information:', '', '', '', ''])
        export_data.append(['Quote Number:', quote_data.get('quote_number', 'N/A'), '', '', ''])
        export_data.append(['Date:', datetime.now().strftime('%B %d, %Y'), '', '', ''])
        export_data.append(['Client:', client_data.get('company', 'N/A'), '', '', ''])
        export_data.append(['Contact:', client_data.get('contact_name', 'N/A'), '', '', ''])
        export_data.append(['Email:', client_data.get('contact_email', 'N/A'), '', '', ''])
        export_data.append(['', '', '', '', ''])
        export_data.append(['SKU', 'Description', 'Quantity', 'Unit Price', 'Total'])
        
        for idx, item in items_df.iterrows():
            sku = str(item.get('sku', 'Unknown'))
            description = str(item.get('product_type', ''))
            quantity = int(item.get('quantity', 1))
            unit_price = float(item.get('price', 0))
            total_price = unit_price * quantity
            export_data.append([sku, description, quantity, unit_price, total_price])
        
        # Add totals
        subtotal = float(quote_data.get('subtotal', 0))
        tax_rate = float(quote_data.get('tax_rate', 0))
        if tax_rate > 1:
            tax_rate_display = tax_rate
        else:
            tax_rate_display = tax_rate * 100
        tax_amount = float(quote_data.get('tax_amount', 0))
        total = float(quote_data.get('total_amount', 0))
        
        export_data.append(['', '', '', 'Subtotal:', subtotal])
        export_data.append(['', '', '', f'Tax ({tax_rate_display:.1f}%):', tax_amount])
        export_data.append(['', '', '', 'TOTAL:', total])
        
        df = pd.DataFrame(export_data)
        df.to_excel(buffer, index=False, header=False)
    
    buffer.seek(0)
    return buffer

# Alias functions for backward compatibility
def generate_excel_quote(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict) -> io.BytesIO:
    """Generate Excel quote - alias for export_quote_to_excel"""
    return export_quote_to_excel(quote_data, items_df, client_data)

def generate_pdf_quote(quote_data: Dict, items_df: pd.DataFrame, client_data: Dict) -> io.BytesIO:
    """Generate PDF quote - alias for export_quote_to_pdf"""
    return export_quote_to_pdf(quote_data, items_df, client_data)