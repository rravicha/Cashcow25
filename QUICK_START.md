# CashCow - Quick Start Guide

## Installation & Setup

### 1. **Activate Virtual Environment**
```powershell
# Navigate to project directory
cd c:\repo\Cashcow25

# Activate virtual environment
.\cashcow_venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\cashcow_venv\Scripts\Activate.ps1
```

### 2. **Install Dependencies**
```powershell
pip install -r requirements.txt
```

### 3. **Verify Installation**
```powershell
# Optional: Verify web UI components
python verify_web_ui.py
```

### 4. **Configure Database**
Make sure your database is running. Default config expects:
- **Host:** localhost
- **Port:** 5432
- **Database:** cashcow
- **User:** postgres
- **Password:** tiger

Edit `app/config.py` if your settings are different.

### 5. **Initialize Database** (First Time Only)
```powershell
# Run migrations if using Alembic
# Or check scripts/init_db.py
python scripts/init_db.py
```

## Running the Application

```powershell
# Make sure virtual environment is activated
python -m app.main
```

The application will start at: **http://localhost:8000**

## Access Points

| URL | Purpose |
|-----|---------|
| `http://localhost:8000/` | **Dashboard** - Main page |
| `http://localhost:8000/upload` | Upload financial data |
| `http://localhost:8000/transactions` | View transactions |
| `http://localhost:8000/accounts` | View accounts |
| `http://localhost:8000/api/docs` | **API Documentation** (Swagger) |

## Web UI Features

### Dashboard
- Overview of accounts, transactions, institutions
- Recent uploads
- Quick action buttons

### File Upload
- Drag-and-drop upload
- Supports: PDF, Excel (.xlsx, .xls), CSV
- Auto-processing with status tracking

### Data Views
- **Accounts** - All connected accounts
- **Transactions** - With pagination and filtering
- **Institutions** - All financial institutions
- **Categories** - Transaction categories

## Design Philosophy

✅ **Professional** - Facebook-style, minimal design
✅ **No Login** - Local, secure-by-default
✅ **Fast** - Lightweight CSS/JavaScript
✅ **Responsive** - Mobile, tablet, desktop
✅ **API-First** - All data via REST API

## File Structure

```
app/
├── web/                          # Web UI module
│   ├── __init__.py
│   └── routes.py                 # Route handlers
├── templates/                    # HTML templates
│   ├── base.html                 # Base layout
│   ├── dashboard.html            # Dashboard
│   ├── upload.html               # Upload page
│   ├── upload_status.html        # Status tracking
│   ├── uploads_list.html         # Upload history
│   ├── accounts.html             # Accounts view
│   ├── transactions.html         # Transactions view
│   ├── institutions.html         # Institutions view
│   ├── categories.html           # Categories view
│   └── error.html                # Error page
├── static/                       # Static assets
│   ├── css/style.css             # Main stylesheet
│   └── js/main.js                # JavaScript utilities
└── ...
```

## Troubleshooting

### Port Already in Use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Template Not Found Error
Ensure the `app/templates` directory exists and templates are in the correct location.

### Static Files Not Loading
Check that `app/static` directory exists with `css/style.css` and `js/main.js`.

### Database Connection Error
Verify PostgreSQL is running and credentials in `app/config.py` are correct.

```powershell
# Test PostgreSQL connection (if psql is installed)
psql -h localhost -U postgres -d cashcow
```

### Import Errors
Make sure all requirements are installed:
```powershell
pip install -r requirements.txt --force-reinstall
```

## Development Tips

- **Hot Reload:** Changes to Python files auto-reload (set in `main.py`)
- **Debug Mode:** `DEBUG=true` in environment for detailed errors
- **Browser Console:** Check browser console (F12) for JavaScript errors
- **API Testing:** Use `/api/docs` for interactive API testing

## Performance Notes

- Uses Bootstrap 5 CDN for speed
- Minimal JavaScript (no heavy frameworks)
- CSS file is optimized and minified-ready
- Dark mode support for reduced eye strain

## Next Steps

1. ✅ Run the application
2. 📤 Upload your first bank statement
3. 📊 View processed transactions
4. 🔍 Explore the data views

## Support

For issues:
1. Check browser console for errors (F12)
2. Check application terminal for stack traces
3. Review `WEB_UI_README.md` for detailed documentation
4. Check `app/config.py` for configuration issues

---

**Happy organizing your finances with CashCow! 💰**
