# Complete Implementation Guide - Turbo Air Equipment Viewer

## Phase 1: Local Setup & Testing

### Step 1: Project Directory Structure
```
turbo-air-viewer/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── create_database.py              # Database initialization script
├── auth.py                        # Authentication module
├── database.py                    # Database operations module
├── sync_manager.py                # Online/offline sync module
├── ui_components.py               # UI component functions
├── export_utils.py                # PDF/Excel export utilities
├── email_service.py               # Email integration module
├── .gitignore                     # Git ignore file
├── .streamlit/
│   ├── config.toml               # Streamlit configuration
│   └── secrets.toml              # Local secrets (don't commit!)
├── turbo_air_products.xlsx        # Product data
├── 2024 List Price Norbaja Copy.xlsx  # Price list
├── turbo_air_db_online.sqlite     # Local SQLite database
├── /pdfs/                         # PDF files directory
└── /pdf_screenshots/              # PDF screenshots directory
    ├── PRO-12R-N(-L)/
    │   ├── page_1.png
    │   └── page_2.png
    └── ... (other product screenshots)
```

### Step 2: Create Virtual Environment & Install Dependencies
```bash
# In your terminal, navigate to project directory
cd turbo-air-viewer

# Activate your existing venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies (will create requirements.txt)
pip install streamlit pandas openpyxl PyMuPDF pillow reportlab supabase sqlite3 msal streamlit-authenticator
```

### Step 3: Local Testing Without Supabase
1. Run `python create_database.py` to create local SQLite database
2. Run `streamlit run app.py`
3. Test all features in offline mode:
   - Browse products
   - Search functionality
   - Add to cart
   - Create clients
   - Generate quotes
4. The app should work completely offline using SQLite

## Phase 2: Supabase Setup

### Step 1: Create Supabase Project
1. Go to [app.supabase.com](https://app.supabase.com)
2. Click "New Project"
3. Fill in:
   - Name: `turbo-air-catalog`
   - Database Password: (save this securely!)
   - Region: Choose closest to you
4. Click "Create Project" and wait ~2 minutes

### Step 2: Get Your Credentials
1. Go to Settings → API
2. Copy these values:
   - Project URL: `https://xxxxx.supabase.co`
   - anon public key: `eyJhbGc...`
   - service_role key: `eyJhbGc...` (keep secret!)

### Step 3: Set Up Database Tables
1. Go to SQL Editor in Supabase
2. Run the schema creation script (provided in create_database.py)
3. This creates tables for:
   - users (managed by Supabase Auth)
   - products
   - clients
   - quotes
   - quote_items
   - cart_items
   - search_history

### Step 4: Enable Authentication Providers
1. Go to Authentication → Providers
2. Enable Email (already enabled by default)
3. For Google:
   - Click "Google" 
   - You need Google Cloud Console credentials
   - Follow Supabase guide for Google OAuth setup
4. For Microsoft:
   - Click "Microsoft"
   - You need Azure AD app registration
   - Follow the Microsoft setup below

### Step 5: Set Up Storage Buckets
1. Go to Storage in Supabase
2. Create bucket: `pdf-screenshots`
3. Make it public (for read access)
4. Set policies for authenticated users

## Phase 3: Microsoft 365 Email Integration

### Step 1: Register App in Azure AD
1. Go to [portal.azure.com](https://portal.azure.com)
2. Navigate to "Azure Active Directory" → "App registrations"
3. Click "New registration"
4. Fill in:
   - Name: `Turbo Air Quote Sender`
   - Supported account types: "Accounts in this organizational directory only"
   - Redirect URI: Leave blank for now
5. Click "Register"

### Step 2: Configure App Permissions
1. In your app, go to "API permissions"
2. Click "Add a permission"
3. Choose "Microsoft Graph"
4. Choose "Application permissions"
5. Search and add: `Mail.Send`
6. Click "Grant admin consent" (requires admin rights)

### Step 3: Create Client Secret
1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Description: `Turbo Air Email`
4. Expires: Choose appropriate duration
5. Copy the secret value immediately (shown only once!)

### Step 4: Get Application Details
Copy these values:
- Application (client) ID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- Directory (tenant) ID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- Client Secret: `your-secret-value`

### Step 5: Configure Microsoft Auth in Supabase (Optional)
1. In Supabase Authentication → Providers → Microsoft
2. Add:
   - Client ID: Your Application ID
   - Secret: Your Client Secret
3. Copy the callback URL and add it to Azure AD app

## Phase 4: Configuration Files

### Step 1: Create .streamlit/secrets.toml (Local Testing)
```toml
[supabase]
url = "https://xxxxx.supabase.co"
anon_key = "your-anon-key"
service_role_key = "your-service-role-key"

[email]
tenant_id = "your-tenant-id"
client_id = "your-client-id"
client_secret = "your-client-secret"
sender_email = "sales@yourcompany.com"

[app]
debug = true
```

### Step 2: Create .gitignore
```
# Secrets
.streamlit/secrets.toml
secrets.toml

# Database
*.sqlite
*.db

# Python
__pycache__/
*.py[cod]
venv/
env/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Temporary
*.tmp
*.log
```

## Phase 5: GitHub Setup

### Step 1: Initialize Git Repository
```bash
# In project directory
git init
git add .
git commit -m "Initial commit"
```

### Step 2: Create GitHub Repository
1. Go to [github.com](https://github.com)
2. Click "New repository"
3. Name: `turbo-air-viewer`
4. Private repository (recommended)
5. Don't initialize with README
6. Create repository

### Step 3: Push to GitHub
```bash
# Add remote origin (use your repository URL)
git remote add origin https://github.com/YOUR_USERNAME/turbo-air-viewer.git

# Push to main branch
git branch -M main
git push -u origin main
```

## Phase 6: Streamlit Cloud Deployment

### Step 1: Connect Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub account
4. Select repository: `turbo-air-viewer`
5. Branch: `main`
6. Main file path: `app.py`

### Step 2: Add Secrets in Streamlit Cloud
1. Click "Advanced settings"
2. In "Secrets" section, paste your secrets.toml content:
```toml
[supabase]
url = "https://xxxxx.supabase.co"
anon_key = "your-anon-key"
service_role_key = "your-service-role-key"

[email]
tenant_id = "your-tenant-id"
client_id = "your-client-id"
client_secret = "your-client-secret"
sender_email = "sales@yourcompany.com"

[app]
debug = false
```

### Step 3: Deploy
1. Click "Deploy"
2. Wait for deployment (5-10 minutes first time)
3. Your app URL: `https://your-app-name.streamlit.app`

## Phase 7: Testing Checklist

### Offline Testing (Local)
- [ ] Products load from SQLite
- [ ] Search works offline
- [ ] Cart operations work
- [ ] Client creation works
- [ ] Quote generation works
- [ ] Excel/PDF export works

### Online Testing (Deployed)
- [ ] User registration/login works
- [ ] Google/Microsoft sign-in works
- [ ] Data syncs to Supabase
- [ ] Multiple devices show same data
- [ ] Email sending works
- [ ] Offline mode switches automatically
- [ ] Data persists after offline/online switch

### User Role Testing
- [ ] Admin can update products
- [ ] Sales can create/edit own clients
- [ ] Distributor can create/edit own clients
- [ ] Users can't see other users' data

## Phase 8: Maintenance & Updates

### To Update the App
1. Make changes locally
2. Test thoroughly
3. Commit and push to GitHub:
```bash
git add .
git commit -m "Description of changes"
git push
```
4. Streamlit Cloud auto-deploys updates

### To Update Product Database
1. Admin users can do it through the app
2. Or update locally and run sync script

### To Monitor Usage
1. Supabase Dashboard shows:
   - Active users
   - Database usage
   - API calls
2. Streamlit Cloud shows:
   - App viewers
   - Resource usage

## Troubleshooting

### Common Issues

1. **"Cannot connect to Supabase"**
   - Check internet connection
   - Verify Supabase credentials
   - Check if Supabase project is paused

2. **"Email not sending"**
   - Verify Microsoft app permissions
   - Check tenant ID and client credentials
   - Ensure sender email is valid

3. **"Offline mode not working"**
   - Check if SQLite database exists
   - Verify sync_manager is initialized
   - Check browser console for errors

4. **"Authentication failing"**
   - Verify redirect URLs in providers
   - Check Supabase auth settings
   - Ensure tokens are not expired

## Security Notes

1. **Never commit secrets.toml to Git**
2. **Use environment-specific keys** (dev/prod)
3. **Regularly rotate secrets**
4. **Monitor Supabase usage** for unusual activity
5. **Keep dependencies updated**