"""
人设数据访问层
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from backend.models.database.tables import UserPersonaTable


class PersonaRepository:
    """人设数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, persona_id: int) -> Optional[UserPersonaTable]:
        """根据ID获取人设"""
        return self.db.query(UserPersonaTable).filter(
            UserPersonaTable.id == persona_id
        ).first()

    def get_user_personas(self, user_id: int, limit: int = 3) -> List[UserPersonaTable]:
        """获取用户的人设列表（最近使用的3条）"""
        return self.db.query(UserPersonaTable).filter(
            UserPersonaTable.user_id == user_id
        ).order_by(desc(UserPersonaTable.last_used_at)).limit(limit).all()

    def get_by_description(self, user_id: int, description: str) -> Optional[UserPersonaTable]:
        """根据描述查找人设"""
        return self.db.query(UserPersonaTable).filter(
            UserPersonaTable.user_id == user_id,
            UserPersonaTable.persona_description == description
        ).first()

    def create(self, user_id: int, description: str) -> UserPersonaTable:
        """创建人设（如果超过3条，删除最旧的）"""
        # 检查是否已存在
        existing = self.get_by_description(user_id, description)
        if existing:
            self.update_last_used(existing)
            return existing

        # 检查数量，超过则删除最旧的
        user_personas = self.get_user_personas(user_id, limit=4)
        if len(user_personas) >= 3:
            # 删除最旧的一条
            oldest = user_personas[-1]
            self.db.delete(oldest)

        # 创建新人设
        persona = UserPersonaTable(
            user_id=user_id,
            persona_description=description,
            last_used_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        self.db.add(persona)
        self.db.commit()
        self.db.refresh(persona)
        return persona

    def update_last_used(self, persona: UserPersonaTable) -> UserPersonaTable:
        """更新最后使用时间"""
        persona.last_used_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(persona)
        return persona

    def delete(self, persona_id: int) -> bool:
        """删除人设"""
        persona = self.get_by_id(persona_id)
        if persona:
            self.db.delete(persona)
            self.db.commit()
            return True
        return False

    def delete_by_user(self, user_id: int) -> int:
        """删除用户的所有人设"""
        count = self.db.query(UserPersonaTable).filter(
            UserPersonaTable.user_id == user_id
        ).delete()
        self.db.commit()
        return count
