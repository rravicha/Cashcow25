# CashCow Web UI - Professional Dashboard

## Overview
A professional, Facebook-style web interface for the CashCow Financial Management System. Clean, minimal design with full functionality for managing financial data.

## Features

### 🏠 Dashboard
- Quick overview of accounts, transactions, and institutions
- Recent uploads summary
- Active accounts listing
- Statistics for last 30 days

### 📤 File Upload
- Drag-and-drop file upload
- Support for PDF, Excel, and CSV files
- Real-time processing status
- Detailed upload history

### 💾 Data Management
- **Accounts** - View and manage financial accounts
- **Transactions** - Browse all transactions with pagination and filtering
- **Institutions** - View all connected institutions
- **Categories** - Organize and manage transaction categories

### 📊 Data Visualization
- Transaction statistics
- Upload processing timeline
- Real-time status updates
- Professional data tables

## Technical Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Jinja2** - HTML template engine
- **SQLAlchemy** - ORM for database operations

### Frontend
- **Bootstrap 5** - Responsive UI framework
- **Bootstrap Icons** - Professional icon set
- **Vanilla JavaScript** - Lightweight interactivity

### Styling
- Clean, minimal design
- Professional color scheme
- Dark mode support (CSS ready)
- Fully responsive (mobile, tablet, desktop)

## Project Structure

```
app/
├── web/
│   ├── __init__.py
│   └── routes.py           # Web route handlers
├── templates/
│   ├── base.html           # Base template with navigation
│   ├── dashboard.html      # Dashboard page
│   ├── upload.html         # File upload page
│   ├── upload_status.html  # Upload status tracking
│   ├── uploads_list.html   # Upload history
│   ├── accounts.html       # Accounts list
│   ├── transactions.html   # Transactions list
│   ├── institutions.html   # Institutions list
│   ├── categories.html     # Categories list
│   └── error.html          # Error page
├── static/
│   ├── css/
│   │   └── style.css       # Main stylesheet
│   └── js/
│       └── main.js         # Utility functions
└── main.py                 # Updated with web UI integration
```

## Navigation

- **Dashboard** (`/`) - Home page with overview
- **Data** Menu:
  - Accounts (`/accounts`)
  - Transactions (`/transactions`)
  - Institutions (`/institutions`)
  - Categories (`/categories`)
- **Upload** Menu:
  - New Upload (`/upload`)
  - Upload History (`/uploads`)
  - Upload Status (`/upload/{job_id}`)

## Running the Application

```bash
# Activate virtual environment
.\cashcow_venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m app.main

# Access in browser
http://localhost:8000
```

## API Integration

The web UI works seamlessly with existing API routes:
- All API endpoints available at `/api/*`
- REST API documentation at `/api/docs`
- Web UI completely separate, no login required

## Design Principles

✅ **No Login** - Local application, direct access
✅ **Professional Look** - Facebook-style, minimal design
✅ **Fast Performance** - Lightweight CSS and JS
✅ **Responsive** - Works on all screen sizes
✅ **Accessible** - Bootstrap icons and semantic HTML
✅ **Dark Mode Ready** - CSS includes dark mode support
✅ **API-First** - All data fetched via existing APIs

## Future Enhancements

- [ ] Export data to Excel/CSV
- [ ] Advanced filtering and search
- [ ] Transaction categorization UI
- [ ] Monthly/yearly reports
- [ ] Charts and visualizations
- [ ] Batch operations

## Support

For issues or questions about the web UI, check:
1. Browser console for JavaScript errors
2. Application logs for backend issues
3. Database connection in `app/config.py`
