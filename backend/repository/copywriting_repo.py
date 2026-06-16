"""口播文案数据访问层"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models.database.copywriting import CopywritingTable


class CopywritingRepository:
    """口播文案数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, copywriting_id: str) -> Optional[CopywritingTable]:
        return self.db.query(CopywritingTable).filter(
            CopywritingTable.copywriting_id == copywriting_id
        ).first()

    def get_by_user(self, user_id: int, limit: int = 20) -> List[CopywritingTable]:
        return self.db.query(CopywritingTable).filter(
            CopywritingTable.user_id == user_id
        ).order_by(desc(CopywritingTable.created_at)).limit(limit).all()

    def create(
        self,
        copywriting_id: str,
        title: str,
        hooks: list,
        content: str,
        mode: str,
        persona: str,
        user_id: int,
    ) -> CopywritingTable:
        cw = CopywritingTable(
            copywriting_id=copywriting_id,
            title=title,
            hooks=hooks,
            content=content,
            mode=mode,
            persona=persona,
            user_id=user_id,
        )
        self.db.add(cw)
        self.db.commit()
        self.db.refresh(cw)
        return cw

    def update(self, cw: CopywritingTable, **kwargs) -> CopywritingTable:
        for field, value in kwargs.items():
            if hasattr(cw, field):
                setattr(cw, field, value)
        self.db.commit()
        self.db.refresh(cw)
        return cw
