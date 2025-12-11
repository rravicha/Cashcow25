# 📝 CashCow Web UI - Quick Reference Card

## ⚡ 30-Second Quick Start

```powershell
# 1. Navigate to project
cd c:\repo\Cashcow25

# 2. Activate virtual environment
.\cashcow_venv\Scripts\Activate.ps1

# 3. Install requirements (if needed)
pip install -r requirements.txt

# 4. Run application
python -m app.main

# 5. Open browser
# → http://localhost:8000
```

---

## 🗺️ Navigation Map

```
DASHBOARD (Home)
├─ 📊 Statistics (4 cards)
├─ ⚡ Quick Actions (4 buttons)
├─ 📤 Recent Uploads (5 latest)
└─ 💾 Active Accounts (10 latest)

DATA MENU
├─ 💾 Accounts → View all accounts
├─ 📋 Transactions → Browse with pagination
├─ 🏦 Institutions → Financial institutions
└─ 🏷️ Categories → Transaction categories

UPLOAD MENU
├─ 📤 New Upload → Upload form with drag-drop
└─ 📁 Upload History → All uploads + status

API
└─ 📚 /api/docs → Swagger API documentation
```

---

## 📂 Key Files

| File | Purpose |
|------|---------|
| `app/web/routes.py` | Web route handlers |
| `app/templates/base.html` | Master template |
| `app/templates/dashboard.html` | Home page |
| `app/static/css/style.css` | All styling |
| `app/static/js/main.js` | JavaScript utilities |
| `app/main.py` | Application entry point |

---

## 🎨 Customization Quick Tips

### Change Colors
Edit `app/static/css/style.css`:
```css
:root {
    --primary-color: #0d6efd;        /* Change this */
    --secondary-color: #6c757d;
    /* ... */
}
```

### Change Port
Edit `app/config.py`:
```python
PORT: int = 8001  # Change from 8000 to 8001
```

### Change App Name
Edit `app/config.py`:
```python
APP_NAME: str = "My Financial App"  # Change from "CashCow..."
```

### Add Custom CSS
Add to `app/static/css/style.css` (keep existing rules)

### Add Navigation Item
Edit `app/templates/base.html` in `<nav>` section

---

## 🐛 Troubleshooting Quick Guide

| Problem | Solution |
|---------|----------|
| Module not found | Activate venv: `.\cashcow_venv\Scripts\Activate.ps1` |
| Port 8000 in use | Change PORT in `app/config.py` |
| Database error | Check PostgreSQL running + credentials in `app/config.py` |
| Template not found | Verify `app/templates/` has all HTML files |
| CSS/JS not loading | Check `app/static/` directory exists |
| Blank page | Check browser console (F12) for errors |

---

## ✅ Feature Checklist

- [x] Dashboard with statistics
- [x] File upload (PDF, Excel, CSV)
- [x] Real-time status tracking
- [x] Transactions view with pagination
- [x] Account filtering
- [x] Institution management
- [x] Category management
- [x] Responsive design
- [x] Professional styling
- [x] No authentication required
- [x] API intact
- [x] Dark mode support

---

## 🔗 URLs at a Glance

```
http://localhost:8000/              Dashboard
http://localhost:8000/upload        Upload page
http://localhost:8000/uploads       Upload history
http://localhost:8000/accounts      Accounts list
http://localhost:8000/transactions  Transactions list
http://localhost:8000/institutions  Institutions list
http://localhost:8000/categories    Categories list
http://localhost:8000/api/docs      API documentation
```

---

## 📊 Project Statistics

- **Templates**: 10 HTML files (1,024 lines)
- **CSS**: 500+ lines (professional styling)
- **JavaScript**: 200+ lines (utilities)
- **Python**: 229 lines (web routes)
- **Setup Time**: < 5 minutes
- **Load Time**: < 1 second

---

## 💡 Developer Cheat Sheet

### Add New Page

1. Create template in `app/templates/mypage.html`
2. Add route in `app/web/routes.py`:
```python
@router.get("/mypage", response_class=HTMLResponse)
async def mypage(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("mypage.html", {"request": request})
```
3. Add navigation link in `app/templates/base.html`

### Use Database

```python
from app.models.dimensions import AccountDim
from sqlalchemy.orm import Session

accounts = db.query(AccountDim).filter(AccountDim.is_current == True).all()
```

### Show Alert

```python
return templates.TemplateResponse("page.html", {
    "request": request,
    "success": "File uploaded successfully!"
})
```

### Add CSS Class

All Bootstrap 5 classes available. Common ones:
- `btn btn-primary` - Primary button
- `card border-0 shadow-sm` - Card
- `row` - Grid row
- `col-md-6` - 6-column width
- `mb-3` - Bottom margin
- `text-danger` - Red text
- `badge bg-success` - Green badge

---

## 🎯 Common Tasks

### Upload Test File
1. Go to `/upload`
2. Drag a PDF/Excel/CSV file
3. Click "Upload & Process"
4. Monitor status in `/upload/{id}`

### View Transactions
1. Go to `/transactions`
2. Select account from dropdown
3. Click "Filter"
4. Browse paginated results

### Check Upload History
1. Go to `/uploads`
2. Click "View" on any upload
3. See detailed status and timeline

### Filter Transactions by Account
1. Go to `/transactions`
2. Select account from dropdown
3. Click "Filter" button
4. Results update automatically

---

## 🚨 Important Notes

⚠️ **Database Required**: PostgreSQL must be running
⚠️ **Virtual Environment**: Always activate before running
⚠️ **Port Conflict**: Change PORT in config if 8000 is used
⚠️ **Static Files**: CSS/JS must be in `app/static/`
⚠️ **No Login**: This is by design for local apps

---

## 📚 Documentation

- **QUICK_START.md** - Detailed setup guide
- **WEB_UI_README.md** - Feature overview
- **WEB_UI_IMPLEMENTATION.md** - Technical details
- **README_WEB_UI.md** - Full summary

---

## 🎓 Tech Stack

- **Backend**: FastAPI + SQLAlchemy
- **Frontend**: Bootstrap 5 + Vanilla JS
- **Database**: PostgreSQL
- **Server**: Uvicorn (ASGI)

---

## ✨ That's All!

You're ready to go! 🚀

Questions? Check the documentation files.

---

**Build Date**: December 10, 2025
**Version**: 1.0.0
**Status**: Production Ready ✅
