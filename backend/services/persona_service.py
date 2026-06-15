"""
人设服务
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.repository.persona_repo import PersonaRepository
from backend.models.domain.persona import PersonaCreate, PersonaResponse

logger = logging.getLogger(__name__)


class PersonaService:
    """人设业务服务"""

    def __init__(self):
        self._repo = None

    def _get_repo(self, db: Session) -> PersonaRepository:
        """获取repository实例"""
        if self._repo is None or self._repo.db != db:
            self._repo = PersonaRepository(db)
        return self._repo

    def get_user_personas(self, db: Session, user_id: int) -> List[PersonaResponse]:
        """获取用户的人设列表"""
        repo = self._get_repo(db)
        personas = repo.get_user_personas(user_id, limit=3)
        return [PersonaResponse.model_validate(p) for p in personas]

    def create_persona(self, db: Session, user_id: int, persona_in: PersonaCreate) -> PersonaResponse:
        """创建人设"""
        repo = self._get_repo(db)
        persona = repo.create(user_id, persona_in.persona_description)
        return PersonaResponse.model_validate(persona)

    def update_persona_last_used(self, db: Session, user_id: int, description: str) -> PersonaResponse:
        """更新人设最后使用时间"""
        repo = self._get_repo(db)
        persona = repo.get_by_description(user_id, description)
        if persona:
            persona = repo.update_last_used(persona)
            return PersonaResponse.model_validate(persona)
        # 不存在则创建
        persona = repo.create(user_id, description)
        return PersonaResponse.model_validate(persona)

    def delete_persona(self, db: Session, persona_id: int) -> bool:
        """删除人设"""
        repo = self._get_repo(db)
        return repo.delete(persona_id)


# 全局实例
persona_service = PersonaService()
