"""
team-memory-server MCP 接口层

职责：将 MemoryStore 的 CRUD 操作封装为 MCP Tool，供 Claude Code / Cursor 调用。
"""

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from memory_db import MemoryStore

# ---------------------------------------------------------------------------
# MCP 服务器实例
# ---------------------------------------------------------------------------
mcp = FastMCP("团队记忆与决策 MCP")

# ---------------------------------------------------------------------------
# 数据层实例
# ---------------------------------------------------------------------------
store = MemoryStore()


# ---------------------------------------------------------------------------
# Pydantic 入参模型
# ---------------------------------------------------------------------------

class AddMemoryInput(BaseModel):
    """新增团队记忆的入参模型"""

    project_name: str = Field(
        ...,
        description="项目名称，用于归类记忆。例如：'claude-code-stack-zh'、'内部ERP系统'",
    )
    decision_content: str = Field(
        ...,
        description="决策或记忆的具体内容。例如：'使用 SQLite 作为本地存储，不引入 PostgreSQL'、'API 统一返回 camelCase'",
    )
    tags: str = Field(
        default="",
        description="逗号分隔的标签，方便后续检索。例如：'架构,数据库,规范'、'前端,性能'",
    )


class GetProjectMemoriesInput(BaseModel):
    """按项目查询记忆的入参模型"""

    project_name: str = Field(
        ...,
        description="要查询的项目名称，将返回该项目下所有记忆记录",
    )


class SearchMemoriesByTagInput(BaseModel):
    """按标签搜索记忆的入参模型"""

    tag: str = Field(
        ...,
        description="要搜索的标签关键词。例如：'架构'、'数据库'、'规范'",
    )


class DeleteMemoryInput(BaseModel):
    """删除记忆的入参模型"""

    memory_id: int = Field(
        ...,
        description="要删除的记忆记录 id",
    )


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def add_team_memory(project_name: str, decision_content: str, tags: str = "") -> str:
    """
    新增一条团队记忆或架构决策记录。

    当需要记录团队的架构决策、技术选型、项目规范、重要讨论结论时使用此工具。
    适合场景：团队做出了一个值得记录的技术决定、确定了项目规范、需要沉淀经验教训。
    记录后可通过项目名称或标签检索回溯。

    Args:
        project_name: 项目名称
        decision_content: 决策或记忆内容
        tags: 逗号分隔的标签

    Returns:
        包含新记录 id 的确认信息
    """
    # 使用 Pydantic 做入参校验
    params = AddMemoryInput(
        project_name=project_name,
        decision_content=decision_content,
        tags=tags,
    )
    record_id = store.add_memory(
        project_name=params.project_name,
        decision_content=params.decision_content,
        tags=params.tags,
    )
    return f"✅ 已记录团队记忆（id={record_id}），项目：{params.project_name}"


@mcp.tool()
def get_project_memories(project_name: str) -> str:
    """
    查询指定项目的全部团队记忆与决策记录。

    当需要回顾某项目的历史架构决策、技术规范、过往结论时使用此工具。
    适合场景：新成员加入项目需要了解历史决策、需要确认某项目的技术选型、
    开发前查阅项目已有的规范和约定。结果按更新时间倒序排列。

    Args:
        project_name: 项目名称

    Returns:
        该项目下所有记忆记录的格式化文本
    """
    params = GetProjectMemoriesInput(project_name=project_name)
    memories = store.get_memories_by_project(project_name=params.project_name)

    if not memories:
        return f"📭 项目「{params.project_name}」暂无记忆记录"

    lines = [f"📋 项目「{params.project_name}」的记忆记录（共 {len(memories)} 条）："]
    for m in memories:
        lines.append(
            f"  [{m['id']}] {m['updated_at']} | 标签：{m['tags']}\n"
            f"       {m['decision_content']}"
        )
    return "\n".join(lines)


@mcp.tool()
def search_memories_by_tag(tag: str) -> str:
    """
    按标签关键词搜索团队记忆。

    当需要跨项目查找某类决策时使用此工具。例如：想知道团队在所有项目中
    关于"数据库"的决策、查找"性能"相关的优化记录、检索"安全"相关的规范。
    适合场景：跨项目横向检索、模糊回忆"好像之前讨论过某个话题"时定位记录。

    Args:
        tag: 标签关键词

    Returns:
        匹配的记忆记录的格式化文本
    """
    params = SearchMemoriesByTagInput(tag=tag)
    memories = store.search_memories_by_tag(tag=params.tag)

    if not memories:
        return f"📭 未找到包含标签「{params.tag}」的记忆记录"

    lines = [f"🔍 标签「{params.tag}」的搜索结果（共 {len(memories)} 条）："]
    for m in memories:
        lines.append(
            f"  [{m['id']}] 项目：{m['project_name']} | "
            f"标签：{m['tags']} | {m['updated_at']}\n"
            f"       {m['decision_content']}"
        )
    return "\n".join(lines)


@mcp.tool()
def delete_team_memory(memory_id: int) -> str:
    """
    删除一条团队记忆记录。

    当需要清除过时、错误或不再适用的决策记录时使用此工具。
    适合场景：某条决策已被推翻需要移除、记录内容有误需要删除后重新添加。
    ⚠️ 删除操作不可逆，请确认 memory_id 正确后再调用。

    Args:
        memory_id: 要删除的记忆记录 id

    Returns:
        删除结果的确认信息
    """
    params = DeleteMemoryInput(memory_id=memory_id)
    success = store.delete_memory(memory_id=params.memory_id)

    if success:
        return f"🗑️ 已删除记忆记录（id={params.memory_id}）"
    else:
        return f"❌ 未找到 id={params.memory_id} 的记忆记录，删除失败"


def main() -> None:
    """MCP 服务器启动入口，供 pyproject.toml [project.scripts] 调用"""
    mcp.run()


# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
