"""
Initialize the database.
Creates all tables defined in the models.
"""

import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from app.database import init_db
from app.config import settings

def main():
    print(f"Initializing database: {settings.DB_NAME} on {settings.DB_HOST}")
    try:
        init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
