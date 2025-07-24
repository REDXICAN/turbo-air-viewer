import os
import fitz  # PyMuPDF
from PIL import Image
import io
from pathlib import Path

def pdf_to_screenshots(pdf_path, output_folder, dpi=200, pages_to_capture=[0, 1]):
    """Convert specified pages of a PDF to high-quality screenshots"""
    try:
        doc = fitz.open(pdf_path)
        pdf_name = Path(pdf_path).stem
        
        # Create a folder for each PDF
        pdf_output_folder = os.path.join(output_folder, pdf_name)
        os.makedirs(pdf_output_folder, exist_ok=True)
        
        for page_num in pages_to_capture:
            if page_num < len(doc):
                page = doc[page_num]
                zoom = dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Naming: filename P.1.png or filename P.2.png
                output_filename = f"{pdf_name} P.{page_num + 1}.png"
                output_path = os.path.join(pdf_output_folder, output_filename)
                img.save(output_path, "PNG", quality=95, optimize=True)
                
                print(f"✓ Saved: {output_filename} in {pdf_name}/")
        
        doc.close()
        return True
        
    except Exception as e:
        print(f"✗ Error processing {pdf_path}: {str(e)}")
        return False

def main():
    # Configuration
    SOURCE_FOLDER = r"O:\OneDrive\Documentos\-- TurboAir\7 Bots\Turbots\-- Turbo Viewer\pdfs"
    OUTPUT_FOLDER = r"O:\OneDrive\Documentos\-- TurboAir\7 Bots\Turbots\-- Turbo Viewer\pdf_screenshots"
    DPI = 200
    PAGES_TO_CAPTURE = [0, 1]
    
    # Check if source folder exists
    if not os.path.exists(SOURCE_FOLDER):
        print(f"Error: Source folder not found: {SOURCE_FOLDER}")
        return
    
    print("PDF to Screenshot Converter")
    print("=" * 50)
    print(f"Source: {SOURCE_FOLDER}")
    print(f"Output: {OUTPUT_FOLDER}")
    print(f"Starting conversion...\n")
    
    # Create output folder
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Statistics
    total_pdfs = 0
    processed_pdfs = 0
    skipped_pdfs = 0
    
    # Process all PDFs
    for root, dirs, files in os.walk(SOURCE_FOLDER):
        rel_path = os.path.relpath(root, SOURCE_FOLDER)
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        
        if pdf_files:
            print(f"\nProcessing folder: {rel_path}")
            
            if rel_path != ".":
                current_output_folder = os.path.join(OUTPUT_FOLDER, rel_path)
            else:
                current_output_folder = OUTPUT_FOLDER
            
            os.makedirs(current_output_folder, exist_ok=True)
            
            for pdf_file in pdf_files:
                total_pdfs += 1
                
                # Skip files containing ESP or ES (Spanish files)
                if 'ESP' in pdf_file.upper() or ' ES ' in pdf_file or pdf_file.upper().endswith(' ES.PDF'):
                    print(f"Skipping Spanish file: {pdf_file}")
                    skipped_pdfs += 1
                    continue
                
                pdf_path = os.path.join(root, pdf_file)
                print(f"Converting: {pdf_file}")
                
                if pdf_to_screenshots(pdf_path, current_output_folder, DPI, PAGES_TO_CAPTURE):
                    processed_pdfs += 1
    
    print("\n" + "=" * 50)
    print(f"Complete! Processed {processed_pdfs}/{total_pdfs} PDFs")
    print(f"Skipped {skipped_pdfs} Spanish files")
    print(f"Screenshots saved to: {OUTPUT_FOLDER}")
    
    # Try to open folder (Windows)
    try:
        os.startfile(OUTPUT_FOLDER)
    except:
        pass

if __name__ == "__main__":
    main()