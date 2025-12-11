"""
Verification script to check if all Web UI components are properly installed.
Run this to verify the setup before starting the application.
"""

import os
import sys
from pathlib import Path

def check_structure():
    """Check if all required directories and files exist."""
    
    base_dir = Path(__file__).parent / "app"
    
    checks = {
        "Web Module": base_dir / "web" / "__init__.py",
        "Web Routes": base_dir / "web" / "routes.py",
        "Templates Dir": base_dir / "templates",
        "Base Template": base_dir / "templates" / "base.html",
        "Dashboard Template": base_dir / "templates" / "dashboard.html",
        "Upload Template": base_dir / "templates" / "upload.html",
        "Upload Status Template": base_dir / "templates" / "upload_status.html",
        "Uploads List Template": base_dir / "templates" / "uploads_list.html",
        "Accounts Template": base_dir / "templates" / "accounts.html",
        "Transactions Template": base_dir / "templates" / "transactions.html",
        "Institutions Template": base_dir / "templates" / "institutions.html",
        "Categories Template": base_dir / "templates" / "categories.html",
        "Error Template": base_dir / "templates" / "error.html",
        "Static CSS Dir": base_dir / "static" / "css",
        "Style CSS": base_dir / "static" / "css" / "style.css",
        "Static JS Dir": base_dir / "static" / "js",
        "Main JS": base_dir / "static" / "js" / "main.js",
    }
    
    print("=" * 60)
    print("CashCow Web UI - Setup Verification")
    print("=" * 60)
    
    all_ok = True
    for name, path in checks.items():
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {name}: {path}")
        if not exists:
            all_ok = False
    
    print("=" * 60)
    
    if all_ok:
        print("✓ All components installed successfully!")
        print("\nNext steps:")
        print("1. Activate virtual environment: .\\cashcow_venv\\Scripts\\Activate.ps1")
        print("2. Install requirements: pip install -r requirements.txt")
        print("3. Run the application: python -m app.main")
        print("4. Open browser: http://localhost:8000")
        return True
    else:
        print("✗ Some components are missing. Please check the paths above.")
        return False

if __name__ == "__main__":
    success = check_structure()
    sys.exit(0 if success else 1)
