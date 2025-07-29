import sys
print(f"Python version: {sys.version}")
print("-" * 50)

# Test core imports
core_packages = {
    'streamlit': 'Streamlit',
    'pandas': 'Pandas',
    'numpy': 'NumPy',
    'openpyxl': 'OpenPyXL',
    'PIL': 'Pillow (PIL)',
    'reportlab': 'ReportLab',
}

optional_packages = {
    'supabase': 'Supabase',
    'msal': 'MSAL (Microsoft Auth)',
    'streamlit_authenticator': 'Streamlit Authenticator',
    'fitz': 'PyMuPDF',
}

print("CORE PACKAGES (Required):")
for module, name in core_packages.items():
    try:
        __import__(module)
        print(f"✓ {name}")
    except ImportError:
        print(f"✗ {name} - MISSING")

print("\nOPTIONAL PACKAGES:")
for module, name in optional_packages.items():
    try:
        __import__(module)
        print(f"✓ {name}")
    except ImportError:
        print(f"✗ {name} - Not installed (app will work without it)")