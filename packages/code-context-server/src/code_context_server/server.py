"""
code-context-server MCP 接口层

职责：将 CodeVectorStore 的索引与检索操作封装为 MCP Tool，供 Claude Code / Cursor 调用。
"""

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from vector_store import CodeVectorStore

# ---------------------------------------------------------------------------
# MCP 服务器实例
# ---------------------------------------------------------------------------
mcp = FastMCP("中文代码库上下文 MCP")

# ---------------------------------------------------------------------------
# 数据层实例
# ---------------------------------------------------------------------------
store = CodeVectorStore()


# ---------------------------------------------------------------------------
# Pydantic 入参模型
# ---------------------------------------------------------------------------

class IndexCodebaseInput(BaseModel):
    """索引代码库的入参模型"""

    dir_path: str = Field(
        ...,
        description="要索引的项目根目录的绝对路径。例如：'/home/user/projects/my-app'、'C:\\Users\\dev\\project'",
    )


class SearchCodeContextInput(BaseModel):
    """语义检索代码上下文的入参模型"""

    query: str = Field(
        ...,
        description="自然语言查询语句，描述你想查找的代码逻辑或功能。"
        "例如：'用户认证的流程是怎样的？'、'数据库连接池在哪里配置的？'、'处理支付回调的函数'",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="返回最相关的代码块数量，默认 5，最大 20",
    )


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def index_codebase(dir_path: str) -> str:
    """
    索引指定目录下的代码库，将代码文件切块并向量化存入数据库。

    ⚠️ 这是一个高耗能操作：会递归遍历整个目录、读取所有支持的代码文件（.py/.js/.ts/.md）、
    进行文本切块和向量计算，可能耗时数分钟（取决于代码库大小）。

    调用时机：
      - 首次接入一个新项目，需要建立代码库索引时
      - 代码库发生重大变更（如大范围重构），需要更新全量索引时
    不应在以下场景调用：
      - 只需查找某段代码（请用 search_code_context）
      - 频繁调用（索引完成后无需重复执行）
      - 代码仅做了少量修改（除非需要全量重建索引）

    索引完成后，即可通过 search_code_context 进行语义检索。

    Args:
        dir_path: 项目根目录路径

    Returns:
        索引结果摘要（入库代码块数量）
    """
    params = IndexCodebaseInput(dir_path=dir_path)
    count = store.index_directory(dir_path=params.dir_path)

    if count == 0:
        return f"⚠️ 目录「{params.dir_path}」中未找到可索引的代码文件（支持 .py/.js/.ts/.md）"

    return (
        f"✅ 代码库索引完成！共入库 {count} 个代码块，目录：{params.dir_path}\n"
        f"现在可以使用 search_code_context 进行语义检索了。"
    )


@mcp.tool()
def search_code_context(query: str, top_k: int = 5) -> str:
    """
    根据自然语言描述，在已索引的代码库中语义检索最相关的代码片段。

    这是日常开发中最常用的工具——通过自然语言描述你想要理解的代码逻辑，
    它会返回最相关的代码片段及其来源（文件路径 + 行号），帮助你快速定位代码。

    典型使用场景：
      - 理解代码逻辑：「用户登录的认证流程是怎样的？」
      - 查找功能实现：「处理支付回调的函数在哪里？」
      - 定位 bug 相关代码：「文件上传失败时做了什么处理？」
      - 了解架构设计：「路由是在哪里注册的？」
      - 寻找配置来源：「Redis 连接参数是从哪里读取的？」

    返回结果包含：代码片段内容、来源文件路径、起始行号。
    你可以根据 file_path 和 start_line 直接跳转到对应位置查看完整上下文。

    Args:
        query: 自然语言查询语句
        top_k: 返回结果数量，默认 5

    Returns:
        匹配的代码片段列表，含文件路径和行号
    """
    params = SearchCodeContextInput(query=query, top_k=top_k)
    results = store.search_context(query=params.query, top_k=params.top_k)

    if not results:
        return "📭 未找到相关代码。可能代码库尚未索引，请先调用 index_codebase 建立索引。"

    lines = [f"🔍 查询「{params.query}」的语义检索结果（共 {len(results)} 条）："]
    for i, r in enumerate(results, 1):
        lines.append(
            f"\n─── 结果 {i} ───\n"
            f"📄 文件：{r['file_path']}  |  行号：{r['start_line']}\n"
            f"{r['content']}"
        )
    return "\n".join(lines)


def main() -> None:
    """MCP 服务器启动入口，供 pyproject.toml [project.scripts] 调用"""
    mcp.run()


# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
