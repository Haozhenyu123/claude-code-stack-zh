<div align="center">

# 🧠 claude-code-stack-zh

**专为中文团队打造的 MCP 工具栈**

让 AI 记住团队决策 · 读懂代码库 · 遵守团队规范

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

</div>

---

## 🎯 解决什么问题？

| 痛点 | 场景 | 本项目如何解决 |
|:-----|:-----|:-------------|
| **AI 没有团队记忆** | 每次对话都要重新解释"我们用 SQLite 不用 PG"、"接口格式必须是 `{code,message,data}`" | team-memory-server 持久化存储团队决策，跨会话共享 |
| **AI 看不到全量代码** | 问"支付回调在哪处理的？"AI 只认识当前打开的文件 | code-context-server 语义检索代码库，返回文件路径+行号 |
| **中文规范无法传递** | 新人和 AI 都不知道 Git 提交怎么写、API 格式怎么定 | 内置中文团队规范模板，复制即用 |

---

## ✨ 核心特性

- 🧠 **团队记忆大脑** — SQLite 持久化存储架构决策、技术选型，按项目/标签检索
- 🔍 **代码上下文大脑** — ChromaDB 向量化代码库，自然语言搜代码，精准到文件+行号
- 📜 **中文规范模板** — API 规范、Git 提交规范、Jira→PR 工作流，大厂级别开箱即用
- 🏠 **零外部依赖** — 不需要 Docker / PostgreSQL / Qdrant，SQLite + ChromaDB 本地运行
- 🤝 **Claude Code / Cursor / Claude Desktop 通用** — 基于 MCP 协议，配置即用

---

## 🆚 与同类项目对比

| 维度 | MCP Server Memory | Knowledge Base MCP | cursor-rules-server | **claude-code-stack-zh** |
|:-----|:------------------|:-------------------|:--------------------|:------------------------|
| 定位 | 通用知识图谱 | 文档知识库检索 | 规则分发机制 | **中文团队一体化编码工具栈** |
| 数据模型 | Entity-Relation-Observation | 文档/向量 | Git 仓库规则文件 | **项目-决策-标签（扁平高效）** |
| 代码感知 | ❌ | ❌ 仅文档 | ❌ | **✅ 文件路径 + 行号** |
| 中文规范 | ❌ | ❌ | ❌ | **✅ API/Git/工作流** |
| 外部依赖 | JSON 文件 | HuggingFace API Key | Git 仓库 | **✅ 零外部依赖** |
| 学习成本 | 高（三元组） | 中 | 低 | **极低（CRUD 即可）** |

---

## 📦 包含的 MCP Server

### team-memory-server — 团队记忆与决策

| Tool | 作用 | 典型场景 |
|:-----|:-----|:---------|
| `add_team_memory` | 新增记忆 | "我们决定用 Redis 做缓存，不用本地缓存" |
| `get_project_memories` | 按项目查询 | 新人了解项目历史决策 |
| `search_memories_by_tag` | 跨项目标签搜索 | "之前所有关于数据库的决策" |
| `delete_team_memory` | 删除过时记忆 | 某条决策已被推翻 |

> 存储：**SQLite** · 零配置 · 数据持久化到本地 `team_memory.db`

### code-context-server — 代码库上下文

| Tool | 作用 | 典型场景 |
|:-----|:-----|:---------|
| `index_codebase` | 索引代码库（⚠️ 高耗能） | 首次接入项目 / 大范围重构后 |
| `search_code_context` | 语义检索代码 | "用户认证流程怎么走的？" |

> 存储：**ChromaDB** · 向量检索 · 数据持久化到本地 `chroma_data/`

---

## 🚀 快速开始

### 前置条件

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** 包管理器

### 1. 克隆 & 安装

```bash
git clone https://github.com/your-username/claude-code-stack-zh.git
cd claude-code-stack-zh
uv sync
```

### 2. 配置 MCP 服务器

#### Claude Code

```bash
# 添加团队记忆服务
claude mcp add team-memory -s user -- uv run --directory /绝对路径/claude-code-stack-zh/packages/team-memory-server/src/team_memory_server server.py

# 添加代码上下文服务
claude mcp add code-context -s user -- uv run --directory /绝对路径/claude-code-stack-zh/packages/code-context-server/src/code_context_server server.py
```

> ⚠️ `claude mcp add` 的 `--directory` 参数可能被 CLI 解析器误识别。如遇问题，直接编辑 `~/.claude.json` 的 `mcpServers` 字段。

#### Cursor

在项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "team-memory": {
      "command": "uv",
      "args": ["run", "--directory", "/绝对路径/claude-code-stack-zh/packages/team-memory-server/src/team_memory_server", "server.py"]
    },
    "code-context": {
      "command": "uv",
      "args": ["run", "--directory", "/绝对路径/claude-code-stack-zh/packages/code-context-server/src/code_context_server", "server.py"]
    }
  }
}
```

#### Claude Desktop

编辑 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "team-memory": {
      "command": "uv",
      "args": ["run", "--directory", "/绝对路径/claude-code-stack-zh/packages/team-memory-server/src/team_memory_server", "server.py"]
    },
    "code-context": {
      "command": "uv",
      "args": ["run", "--directory", "/绝对路径/claude-code-stack-zh/packages/code-context-server/src/code_context_server", "server.py"]
    }
  }
}
```

### 3. 验证

```bash
# Claude Code 用户
claude mcp list
# 应显示两个服务 ✓ Connected

# 手动测试
cd packages/team-memory-server/src/team_memory_server
uv run server.py
```

### 4. 开始使用

在 Claude Code / Cursor 对话中：

- 💬 *"帮我们记录一条团队决策：用户认证统一使用 JWT，token 有效期 2 小时"*
- 💬 *"查一下项目之前关于数据库的决策"*
- 💬 *"索引一下 /home/user/my-project 这个代码库"*
- 💬 *"搜索支付回调的代码在哪里"*

---

## 📐 规则库与场景模板

`rules_and_templates/` 提供开箱即用的中文团队规范：

| 文件 | 用途 | 使用方法 |
|:-----|:-----|:---------|
| `standard-api.cursorrules` | RESTful API 规范（统一响应体、错误码、异常处理、分页） | 复制到项目根目录 |
| `git-commit.cursorrules` | Git 提交规范（Angular 中英双语、scope 强制、6 种禁止写法） | 复制到项目根目录 |
| `jira-to-pr-template.md` | Jira→提测全流程模板（5 步工作流，含 MCP Tool 调用指引） | 对话中引用 |

```bash
# 复制规范到你的项目
cp rules_and_templates/standard-api.cursorrules /你的项目/.cursorrules
cp rules_and_templates/git-commit.cursorrules /你的项目/.cursorrules

# 或合并多个规范
cat rules_and_templates/*.cursorrules > /你的项目/.cursorrules
```

---

## 🏗️ 项目结构

```
claude-code-stack-zh/
├── pyproject.toml                       # uv workspace 根配置
├── start.sh                             # 一键启动脚本 (macOS/Linux)
├── LICENSE                              # MIT
├── README.md
├── .gitignore
├── rules_and_templates/                 # 中文规则库
│   ├── standard-api.cursorrules         #   API 开发规范
│   ├── git-commit.cursorrules           #   Git 提交规范
│   └── jira-to-pr-template.md           #   工作流模板
└── packages/
    ├── team-memory-server/              # 团队记忆 MCP 服务
    │   ├── pyproject.toml
    │   └── src/team_memory_server/
    │       ├── server.py                #   MCP 接口层 (FastMCP)
    │       ├── memory_db.py             #   SQLite CRUD 层
    │       └── __init__.py
    └── code-context-server/             # 代码上下文 MCP 服务
        ├── pyproject.toml
        └── src/code_context_server/
            ├── server.py                #   MCP 接口层 (FastMCP)
            ├── vector_store.py          #   ChromaDB 向量存储层
            └── __init__.py
```

---

## 🛠️ 技术栈

| 组件 | 技术 | 说明 |
|:-----|:-----|:-----|
| MCP 协议 | [FastMCP](https://github.com/jlowin/fastmcp) | MCP Tool 注册与调用 |
| 向量数据库 | [ChromaDB](https://www.trychroma.com/) | 代码块向量化与语义检索 |
| 关系数据库 | SQLite | 团队决策持久化（Python 内置） |
| 包管理 | [uv](https://docs.astral.sh/uv/) workspace | Monorepo 依赖管理 |
| 入参校验 | [Pydantic](https://docs.pydantic.dev/) v2 | 强类型 + 自动文档生成 |

---

## 🗺️ Roadmap

- [ ] team-memory-server 支持记忆更新（而非仅删除后重建）
- [ ] code-context-server 增量索引（仅索引变更文件）
- [ ] 支持 .vue / .jsx / .go / .java 等更多语言
- [ ] MCP Prompt 模板（预置常见场景的 Prompt）
- [ ] Docker Compose 一键部署方案

---

## 🤝 参与贡献

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交变更：遵循 `git-commit.cursorrules` 中的 Angular 规范
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

---

## 📄 License

[MIT](./LICENSE) © 2026 claude-code-stack-zh contributors
