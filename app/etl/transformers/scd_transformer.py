"""
SCD Type 2 Transformer.
Handles dimension updates and versioning.
"""

from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, Type, TypeVar

from app.database import Base
from app.models.dimensions import InstitutionDim, AccountDim

T = TypeVar('T', bound=Base)

class SCDTransformer:
    """
    Manages Slowly Changing Dimensions (Type 2).
    """
    
    def __init__(self, db: Session):
        self.db = db

    def upsert_dimension(self, model: Type[T], business_keys: Dict[str, Any], attributes: Dict[str, Any]) -> T:
        """
        Update or insert a dimension record with SCD Type 2 logic.
        1. Find current active record.
        2. If exists and attributes changed -> Close old, Create new.
        3. If attributes same -> Do nothing, return current.
        4. If not exists -> Create new.
        """
        # Find current
        query = self.db.query(model).filter_by(is_current=True, **business_keys)
        current = query.first()
        
        if not current:
            # Create new
            new_record = model(
                **business_keys,
                **attributes,
                is_current=True,
                valid_from=date.today()
            )
            self.db.add(new_record)
            self.db.commit()
            self.db.refresh(new_record)
            return new_record
            
        # Check for changes
        changed = False
        for key, value in attributes.items():
            if getattr(current, key) != value:
                changed = True
                break
        
        if changed:
            # Close old
            current.is_current = False
            current.valid_to = date.today()
            
            # Create new
            new_record = model(
                **business_keys,
                **attributes,
                is_current=True,
                valid_from=date.today()
            )
            self.db.add(new_record)
            self.db.commit()
            self.db.refresh(new_record)
            return new_record
            
        return current
