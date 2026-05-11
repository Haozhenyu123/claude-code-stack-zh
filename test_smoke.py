"""
本地冒烟测试：验证两个 MCP Server 的数据层逻辑是否正常工作

不依赖 uv / fastmcp / chromadb，仅测试 SQLite 层（team-memory-server）。
code-context-server 的 ChromaDB 层因环境限制无法在此测试，需要本地环境验证。

运行方式：python test_smoke.py
"""

import io
import sys

# Windows 控制台 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import sys
import tempfile
import shutil

# 将子包源码加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "team-memory-server", "src"))

from team_memory_server.memory_db import MemoryStore


def test_team_memory():
    """测试 team-memory-server 的 MemoryStore CRUD"""

    # 使用临时目录，测试完自动清理
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "test_team_memory.db")

    try:
        store = MemoryStore(db_path=db_path)
        print("✅ MemoryStore 初始化成功")

        # ── 测试 add_memory ──
        id1 = store.add_memory(
            project_name="claude-code-stack-zh",
            decision_content="本项目使用 SQLite 存储团队记忆，ChromaDB 存储代码向量",
            tags="架构,数据库,选型",
        )
        print(f"✅ add_memory 成功，id={id1}")

        id2 = store.add_memory(
            project_name="claude-code-stack-zh",
            decision_content="API 统一使用 {code, message, data} 响应体格式",
            tags="规范,API",
        )
        print(f"✅ add_memory 成功，id={id2}")

        id3 = store.add_memory(
            project_name="内部ERP系统",
            decision_content="前端使用 Vue3 + Element Plus，后端 NestJS",
            tags="架构,前端,选型",
        )
        print(f"✅ add_memory 成功，id={id3}")

        # ── 测试 get_memories_by_project ──
        memories = store.get_memories_by_project("claude-code-stack-zh")
        assert len(memories) == 2, f"期望 2 条记录，实际 {len(memories)} 条"
        print(f"✅ get_memories_by_project 成功，返回 {len(memories)} 条记录")

        # ── 测试 search_memories_by_tag ──
        # 搜索标签"架构"，应命中 2 条（id1 和 id3）
        results = store.search_memories_by_tag("架构")
        assert len(results) == 2, f"期望 2 条记录，实际 {len(results)} 条"
        print(f"✅ search_memories_by_tag('架构') 成功，返回 {len(results)} 条记录")

        # 搜索标签"规范"，应命中 1 条（id2）
        results = store.search_memories_by_tag("规范")
        assert len(results) == 1, f"期望 1 条记录，实际 {len(results)} 条"
        print(f"✅ search_memories_by_tag('规范') 成功，返回 {len(results)} 条记录")

        # 搜索标签"数据库"，应命中 1 条（id1）
        results = store.search_memories_by_tag("数据库")
        assert len(results) == 1, f"期望 1 条记录，实际 {len(results)} 条"
        print(f"✅ search_memories_by_tag('数据库') 成功，返回 {len(results)} 条记录")

        # ── 测试 delete_memory ──
        success = store.delete_memory(id2)
        assert success, "删除应返回 True"
        print(f"✅ delete_memory(id={id2}) 成功")

        # 验证删除后只剩 1 条
        memories = store.get_memories_by_project("claude-code-stack-zh")
        assert len(memories) == 1, f"删除后应剩 1 条，实际 {len(memories)} 条"
        print(f"✅ 删除后查询确认：剩余 {len(memories)} 条记录")

        # 删除不存在的记录
        success = store.delete_memory(99999)
        assert not success, "删除不存在的记录应返回 False"
        print(f"✅ delete_memory(不存在的id) 正确返回 False")

        print("\n" + "=" * 50)
        print("🎉 team-memory-server 数据层测试全部通过！")
        print("=" * 50)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_team_memory()
