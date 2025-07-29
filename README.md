# Turbo Air Equipment Viewer

A mobile-first equipment catalog and quote generation system for Turbo Air commercial refrigeration products. Built with Streamlit, Supabase, and designed for both online and offline operation.

## Features

- 📱 **Mobile-First Design** - iOS-style interface optimized for all devices
- 🔄 **Online/Offline Mode** - Works seamlessly with or without internet
- 🛒 **Shopping Cart** - Add products and generate professional quotes
- 📊 **Export Options** - Generate Excel and PDF quotes
- 📧 **Email Integration** - Send quotes directly to clients
- 👥 **Multi-User Support** - Role-based access (Admin, Sales, Distributor)
- 🔍 **Smart Search** - Search by SKU, description, or product type
- 📈 **Dashboard** - Track clients, quotes, and activity

## Technology Stack

- **Frontend**: Streamlit with custom mobile-first UI
- **Backend**: Supabase (PostgreSQL) with offline SQLite fallback
- **Authentication**: Custom auth with session management
- **Export**: ReportLab (PDF), OpenPyXL (Excel)
- **Email**: SMTP integration (Gmail)

## Project Structure

```
turbo-air-viewer/
├── app.py                    # Main application entry point
├── src/                      # Core application modules
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── auth.py              # Authentication module
│   ├── database.py          # Database operations
│   ├── sync.py              # Online/offline sync
│   ├── ui.py                # UI components
│   ├── pages.py             # Page components
│   ├── export.py            # Excel/PDF export
│   ├── email.py             # Email service
│   └── database/
│       ├── __init__.py
│       └── create_db.py     # Database initialization
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── .streamlit/
│   └── config.toml          # Streamlit configuration
└── pdf_screenshots/         # Product images (optional)
```

## Quick Start

### 1. Local Development

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/turbo-air-viewer.git
cd turbo-air-viewer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### 2. Configuration

Create `.streamlit/secrets.toml` (never commit this file):

```toml
[supabase]
url = "https://your-project.supabase.co"
anon_key = "your-anon-key"

[email]
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "your-email@gmail.com"
sender_password = "your-app-password"

[app]
debug = false
```

### 3. Database Setup

The app automatically creates a local SQLite database on first run. For Supabase:

1. Create a new Supabase project
2. Run the SQL schema from `src/database/create_db.py`
3. Add your Supabase credentials to `secrets.toml`

## Deployment

### GitHub Setup

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/turbo-air-viewer.git
git push -u origin main
```

### Streamlit Cloud

1. Connect your GitHub repository to [Streamlit Cloud](https://share.streamlit.io)
2. Add secrets in the Streamlit Cloud dashboard
3. Deploy!

## Security Best Practices

1. **Never commit secrets** - Use `.gitignore` and Streamlit secrets
2. **Use environment-specific keys** - Different keys for dev/prod
3. **Enable RLS** - Row Level Security in Supabase
4. **Regular updates** - Keep dependencies updated

## Features in Detail

### Authentication
- Email/password authentication
- Remember me functionality
- Session management with secure tokens
- Role-based access control

### Product Management
- Browse by category and subcategory
- Search with instant results
- Detailed product specifications
- Product image support

### Quote Generation
- Add products to cart
- Adjust quantities
- Generate professional quotes
- Export to Excel/PDF
- Email quotes to clients

### Offline Capability
- Full functionality without internet
- Automatic sync when connection restored
- Local data persistence
- Seamless mode switching

## Troubleshooting

### Common Issues

**"Cannot connect to Supabase"**
- Verify credentials in secrets.toml
- Check if Supabase project is active
- Ensure internet connection

**"Email not sending"**
- Use Gmail App Password (not regular password)
- Check SMTP settings
- Verify sender email

**"Products not loading"**
- Ensure turbo_air_products.xlsx exists
- Check database initialization
- Verify product data format

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is proprietary software for Turbo Air Inc.

## Support

For support, email support@turboair.com or contact your system administrator.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Database by [Supabase](https://supabase.com)
- Icons and design inspired by iOS Human Interface Guidelines