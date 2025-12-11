"""
Service for managing transaction categories.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session

from app.models.dimensions import CategoryDim
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_category(self, category_id: int) -> Optional[CategoryDim]:
        """Get category by ID."""
        return self.db.query(CategoryDim).filter(CategoryDim.id == category_id).first()

    def get_all_categories(self, category_type: Optional[str] = None) -> List[CategoryDim]:
        """Get all categories, optionally filtered by type."""
        query = self.db.query(CategoryDim).filter(CategoryDim.is_current == True)
        
        if category_type:
            query = query.filter(CategoryDim.category_type == category_type)
            
        return query.all()

    def create_category(self, category: CategoryCreate) -> CategoryDim:
        """Create a new category."""
        db_category = CategoryDim(
            name=category.name,
            category_code=category.category_code,
            parent_category=category.parent_category,
            description=category.description,
            category_type=category.category_type,
            icon=category.icon,
            color=category.color,
            keywords=category.keywords,
            is_current=True,
            valid_from=date.today()
        )
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category

    def update_category(self, category_id: int, category_update: CategoryUpdate) -> Optional[CategoryDim]:
        """Update a category."""
        # Simple update for now (not SCD for categories yet)
        db_category = self.get_category(category_id)
        if not db_category:
            return None
            
        update_data = category_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)
            
        self.db.commit()
        self.db.refresh(db_category)
        return db_category
