"""
team-memory-server 数据层：SQLite CRUD 操作类

职责：纯数据逻辑层，负责团队记忆的增删查改，不涉及任何 MCP 协议逻辑。
"""

import sqlite3
from typing import Optional


class MemoryStore:
    """
    团队记忆存储类

    基于 SQLite 实现对 team_memories 表的 CRUD 操作。
    使用上下文管理器管理数据库连接，确保连接安全关闭。

    表结构:
        id               INTEGER   主键，自增
        project_name     TEXT      项目名称
        decision_content TEXT      决策 / 记忆内容
        tags             TEXT      标签，逗号分隔（如 "架构,数据库,缓存"）
        updated_at       TIMESTAMP 默认当前时间，自动更新
    """

    def __init__(self, db_path: str = "team_memory.db") -> None:
        """
        初始化存储实例。

        Args:
            db_path: SQLite 数据库文件路径，默认为当前目录下的 team_memory.db
        """
        self.db_path = db_path
        # 首次初始化时确保表已创建
        self._ensure_table()

    def _ensure_table(self) -> None:
        """
        确保 team_memories 表存在。

        如果表不存在则创建，包含以下字段：
          - id: 自增主键
          - project_name: 项目名称
          - decision_content: 决策内容
          - tags: 逗号分隔的标签
          - updated_at: 更新时间，默认当前时间，记录更新时自动刷新
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS team_memories (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name     TEXT    NOT NULL,
                    decision_content TEXT    NOT NULL,
                    tags             TEXT    DEFAULT '',
                    updated_at       TIMESTAMP DEFAULT (datetime('now', 'localtime'))
                )
            """)
            conn.commit()

    def add_memory(
        self,
        project_name: str,
        decision_content: str,
        tags: str = "",
    ) -> int:
        """
        新增一条团队记忆。

        Args:
            project_name:     项目名称
            decision_content: 决策 / 记忆内容
            tags:             逗号分隔的标签字符串，如 "架构,性能,缓存"

        Returns:
            新插入记录的自增 id
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO team_memories (project_name, decision_content, tags)
                VALUES (?, ?, ?)
                """,
                (project_name, decision_content, tags),
            )
            conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def get_memories_by_project(self, project_name: str) -> list[dict]:
        """
        根据项目名称查询所有相关记忆，按更新时间倒序排列。

        Args:
            project_name: 项目名称

        Returns:
            匹配的记录列表，每条记录为字典格式：
            {"id": int, "project_name": str, "decision_content": str, "tags": str, "updated_at": str}
        """
        with sqlite3.connect(self.db_path) as conn:
            # 让查询结果以字典形式返回，而非默认的元组
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, project_name, decision_content, tags, updated_at
                FROM team_memories
                WHERE project_name = ?
                ORDER BY updated_at DESC
                """,
                (project_name,),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def search_memories_by_tag(self, tag: str) -> list[dict]:
        """
        根据标签搜索记忆。

        采用模糊匹配策略：由于 tags 字段以逗号分隔存储，
        使用 LIKE 进行匹配，同时兼容以下边界情况：
          - tag 位于字符串开头
          - tag 位于字符串中间
          - tag 位于字符串末尾
          - tags 字段仅包含单个标签

        Args:
            tag: 要搜索的标签关键词

        Returns:
            匹配的记录列表，按更新时间倒序排列，字典格式
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # 匹配三种情况：tag在开头/中间/末尾，以及恰好等于tag
            cursor = conn.execute(
                """
                SELECT id, project_name, decision_content, tags, updated_at
                FROM team_memories
                WHERE tags = ?
                   OR tags LIKE ?
                   OR tags LIKE ?
                   OR tags LIKE ?
                ORDER BY updated_at DESC
                """,
                (
                    tag,                        # 精确匹配：只有一个标签的情况
                    f"{tag},%",                 # 标签在开头：如 "架构,数据库,..."
                    f"%,{tag},%",               # 标签在中间：如 "前端,架构,数据库"
                    f"%,{tag}",                 # 标签在末尾：如 "前端,架构"
                ),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def delete_memory(self, memory_id: int) -> bool:
        """
        根据记录 id 删除一条记忆。

        Args:
            memory_id: 要删除的记录 id

        Returns:
            True 表示成功删除至少一条记录，False 表示未找到对应记录
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM team_memories
                WHERE id = ?
                """,
                (memory_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
