"""
刷新令牌清理服务
定期清理已过期和已撤销的令牌记录
"""
import logging
from datetime import datetime
from typing import Dict
from sqlalchemy.orm import Session

from backend.models.database.tables import TokenBlacklistTable

logger = logging.getLogger(__name__)


class TokenCleanupService:
    """令牌清理服务"""

    @staticmethod
    def cleanup_expired_and_revoked(db: Session) -> Dict[str, int]:
        """
        清理已过期的刷新令牌记录。

        删除 expires_at < now 的所有行（无论 is_revoked 状态）。
        已过期且已撤销的行安全删除；已过期但未撤销的行也无保留价值。
        未过期但已撤销的行保留，以便后续 refresh 请求能返回"已撤销"错误。

        Returns:
            {"expired_deleted": n, "revoked_deleted": n, "total_deleted": n}
        """
        now = datetime.utcnow()

        expired_count = (
            db.query(TokenBlacklistTable)
            .filter(TokenBlacklistTable.expires_at < now,
                    TokenBlacklistTable.is_revoked == False)
            .count()
        )
        revoked_expired_count = (
            db.query(TokenBlacklistTable)
            .filter(TokenBlacklistTable.expires_at < now,
                    TokenBlacklistTable.is_revoked == True)
            .count()
        )

        deleted = (
            db.query(TokenBlacklistTable)
            .filter(TokenBlacklistTable.expires_at < now)
            .delete()
        )
        db.commit()

        logger.info(
            f"令牌清理完成: 删除 {deleted} 条记录 "
            f"(过期: {expired_count}, 已撤销+过期: {revoked_expired_count})"
        )
        return {
            "expired_deleted": expired_count,
            "revoked_deleted": revoked_expired_count,
            "total_deleted": deleted,
        }


token_cleanup_service = TokenCleanupService()
