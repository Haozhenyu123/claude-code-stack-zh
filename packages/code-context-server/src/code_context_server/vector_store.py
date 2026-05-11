"""
code-context-server 数据层：ChromaDB 向量存储与检索

职责：纯数据逻辑层，负责代码文件的索引（向量化入库）与语义检索。
不涉及任何 MCP 协议逻辑，仅依赖 chromadb 和 Python 标准库。
"""

import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings


# 支持索引的文件后缀
SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".md"}

# 需要忽略的目录名
IGNORED_DIRS = {"node_modules", ".git", "venv", ".venv", "__pycache__", "dist", "build"}

# 每个代码块的近似字符数
CHUNK_SIZE = 500


class CodeVectorStore:
    """
    代码向量存储类

    基于 ChromaDB 实现代码文件的切块、向量化与语义检索。
    使用本地持久化客户端，数据保存在 ./chroma_data 目录。
    """

    def __init__(self, persist_path: str = "./chroma_data") -> None:
        """
        初始化向量存储实例。

        Args:
            persist_path: ChromaDB 持久化目录路径，默认为当前目录下的 chroma_data
        """
        self.persist_path = persist_path
        # 创建持久化客户端（数据写入磁盘，进程重启后不丢失）
        self.client = chromadb.PersistentClient(path=persist_path)
        # 获取或创建名为 code_base 的集合，使用 ChromaDB 默认嵌入模型
        self.collection = self.client.get_or_create_collection(
            name="code_base",
        )

    def index_directory(self, dir_path: str) -> int:
        """
        递归遍历指定目录，读取支持的代码文件并切块入库。

        处理流程：
          1. 递归遍历 dir_path，跳过 IGNORED_DIRS 中的目录
          2. 仅处理 SUPPORTED_EXTENSIONS 后缀的文件
          3. 将文件内容按 ~500 字符切块（尽量按换行符切分）
          4. 批量写入 ChromaDB，每条记录附带 file_path 和 start_line 元数据

        Args:
            dir_path: 要索引的目录路径

        Returns:
            本次成功入库的代码块数量
        """
        dir_path = os.path.abspath(dir_path)
        documents: list[str] = []       # 代码块文本
        metadatas: list[dict] = []     # 每条代码的元数据
        ids: list[str] = []            # ChromaDB 文档唯一 id

        # 用于生成唯一 id 的计数器
        chunk_counter = 0

        # ── 第一步：递归收集所有需要索引的文件 ──────────────────
        for root, dirs, files in os.walk(dir_path):
            # 就地修改 dirs，跳过忽略目录（os.walk 不会进入被跳过的目录）
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file_name in files:
                file_ext = os.path.splitext(file_name)[1].lower()
                if file_ext not in SUPPORTED_EXTENSIONS:
                    continue

                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, dir_path)

                # ── 第二步：读取文件内容并按换行符切块 ──────────
                try:
                    with open(file_path, encoding="utf-8", errors="replace") as f:
                        content = f.read()
                except (OSError, UnicodeDecodeError):
                    # 无法读取的文件直接跳过
                    continue

                # 按 ~500 字符切块，尽量在换行符处切分以保持代码完整性
                chunks = self._split_into_chunks(content)

                # ── 第三步：为每个代码块生成元数据 ──────────────
                for idx, chunk_text in enumerate(chunks):
                    # 估算起始行号：根据前面块的总字符数估算
                    preceding_chars = sum(len(c) for c in chunks[:idx])
                    start_line = content[:preceding_chars].count("\n") + 1

                    chunk_counter += 1
                    doc_id = f"{relative_path}_{idx}"

                    documents.append(chunk_text)
                    metadatas.append({
                        "file_path": relative_path,
                        "start_line": start_line,
                    })
                    ids.append(doc_id)

        # ── 第四步：批量写入 ChromaDB ──────────────────────────
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )

        return len(documents)

    def _split_into_chunks(self, text: str) -> list[str]:
        """
        将文本按 ~500 字符切块，尽量在换行符处切分以保持代码完整性。

        策略：
          1. 优先在换行符（\\n）处切分，避免切断一行代码
          2. 如果某行超过 CHUNK_SIZE，强制切分（不太可能，但兜底）
          3. 返回切块列表，每个块尽量接近 CHUNK_SIZE 字符

        Args:
            text: 待切分的文件全文

        Returns:
            切块后的字符串列表
        """
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for line in text.splitlines(keepends=True):
            line_len = len(line)

            # 如果当前行本身超过 CHUNK_SIZE，强制切分这一行
            if line_len > CHUNK_SIZE:
                # 先把之前累积的块存起来
                if current_chunk:
                    chunks.append("".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                # 将超长行按 CHUNK_SIZE 强行切分
                for i in range(0, len(line), CHUNK_SIZE):
                    chunks.append(line[i : i + CHUNK_SIZE])
                continue

            # 如果加入这一行会超过 CHUNK_SIZE，先存当前块，再开始新块
            if current_len + line_len > CHUNK_SIZE and current_chunk:
                chunks.append("".join(current_chunk))
                current_chunk = []
                current_len = 0

            current_chunk.append(line)
            current_len += line_len

        # 把最后一块加进去
        if current_chunk:
            chunks.append("".join(current_chunk))

        return chunks

    def search_context(self, query: str, top_k: int = 5) -> list[dict]:
        """
        根据自然语言查询在 ChromaDB 中检索最相关的代码块。

        Args:
            query: 自然语言查询语句，例如"哪里定义了数据库连接？"
            top_k: 返回最相关的 top_k 条结果，默认 5

        Returns:
            字典列表，每个字典包含：
                - content:    代码块文本
                - file_path:  来源文件路径（相对于索引目录）
                - start_line: 在文件中的估算起始行号
        """
        # ChromaDB 的 query 返回嵌套结构，results["documents"][0] 是文档列表
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
        )

        output: list[dict] = []

        # results 中 documents / metadatas / ids 都是两层列表（因为 query_texts 是列表）
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        for doc, meta in zip(docs, metas):
            output.append({
                "content": doc,
                "file_path": meta.get("file_path", "unknown"),
                "start_line": meta.get("start_line", 0),
            })

        return output
