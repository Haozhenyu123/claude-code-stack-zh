# 场景工作流模板：从任务到提测

> 本模板指导 Claude Code / Cursor 完成"接收任务 → 代码开发 → 提交 PR"的全流程。
> 每一步都必须严格执行，不可跳过。

---

## 步骤 1：读取任务描述，提炼核心需求

### 操作

1. 接收用户输入的 Jira / 任务描述 / 产品需求文档。
2. 提炼出以下要素：

| 要素 | 说明 | 示例 |
|------|------|------|
| 需求目标 | 一句话说清楚要做什么 | "新增订单批量导出接口" |
| 功能范围 | 涉及哪些模块 | 订单模块、文件服务 |
| 业务规则 | 关键约束条件 | 单次最多导出 10 万条、支持 CSV/Excel 格式 |
| 非功能需求 | 性能、安全等 | 流式返回、大数据集不 OOM |

3. 将提炼结果以结构化格式输出给用户确认，**未经确认不得进入下一步**。

### 输出格式

```
📋 需求摘要
目标：{一句话描述}
范围：{涉及模块}
业务规则：
  - {规则 1}
  - {规则 2}
非功能需求：
  - {需求 1}
请确认是否正确，我将开始代码开发。
```

---

## 步骤 2：搜索代码库，理解现有逻辑

### 操作

1. 调用 `search_code_context` MCP 工具，用自然语言搜索当前代码库中与需求相关的逻辑。

   **至少执行 2-3 次不同角度的搜索**，覆盖以下方面：

   | 搜索角度 | 示例 query |
   |---------|-----------|
   | 现有实现 | "订单查询接口是怎么实现的？" |
   | 相关模型 | "订单的数据模型定义在哪里？" |
   | 类似功能 | "现有的导出功能是怎么做的？" |
   | 依赖服务 | "文件上传和下载的逻辑在哪里？" |

2. 根据搜索结果，梳理出现有代码的**调用链路**和**数据流向**。
3. 确定需要新增/修改的文件清单。

### 输出格式

```
🔍 代码库分析结果
现有逻辑：
  - 订单查询：GET /api/orders → OrderController.list() → OrderService.findPage()
  - 数据模型：OrderEntity (src/modules/order/entity/order.entity.ts)
  - 类似功能：用户导出已有实现（UserExportService）

需要变更的文件：
  - 新增：src/modules/order/service/order-export.service.ts
  - 修改：src/modules/order/controller/order.controller.ts
  - 修改：src/modules/order/module/order.module.ts
```

---

## 步骤 3：编写代码，严格遵守 API 规范

### 操作

1. 根据步骤 1 和步骤 2 的分析，开始编写代码。
2. **所有代码必须严格遵守 `standard-api.cursorrules` 中的规范**，重点检查：

   | 规范项 | 检查点 |
   |--------|--------|
   | 响应体格式 | 返回值必须是 `{ code, message, data }` |
   | 错误码 | 业务错误码与 HTTP 状态码分离，使用集中定义的 ErrorCode |
   | 异常处理 | 使用 BusinessException，严禁裸抛异常 |
   | 分页格式 | 入参 { page, pageSize }，出参 { list, total, page, pageSize } |
   | 路径命名 | RESTful 风格，禁止动词路径 |

3. 编写完成后，进行自检：

```
✅ 规范自检
[ ] 响应体是否为 { code, message, data } 格式？
[ ] 错误码是否使用 ErrorCode 常量，而非硬编码？
[ ] 是否通过 BusinessException 抛出业务异常？
[ ] 分页接口入参/出参是否符合规范？
[ ] 接口路径是否为 RESTful 风格？
```

---

## 步骤 4：Git 提交，严格遵守提交规范

### 操作

1. 按照 `git-commit.cursorrules` 规范编写 commit message。
2. 格式：`<type>(<scope>): <中文subject>`
3. body 用英文描述技术细节。

### 提交命令

```bash
git add <变更文件>
git commit -m "type(scope): 中文概括" -m "English technical details..."
```

### 示例

```bash
git add src/modules/order/
git commit -m "feat(order): 新增批量导出订单接口" -m "Add POST /api/orders/export endpoint with streaming CSV response. Supports filtering by date range and order status. Reuses UserExportService pattern for consistency." -m "JIRA: PROJ-1234"
```

---

## 步骤 5：生成标准 PR 描述

### 操作

在提交代码后，自动生成以下格式的 PR 描述，供人工确认后提交。

### PR 描述模板

```markdown
## 📌 需求背景

{Jira 链接或任务描述的简要概述，1-2 句话说明为什么做这个需求}

## 🔧 改动点

- **新增**：{新增了什么文件/接口/功能}
- **修改**：{修改了什么现有逻辑}
- **删除**：{删除了什么废弃代码}（如有）

### 接口变更

| Method | Path | 说明 |
|--------|------|------|
| POST | /api/orders/export | 新增订单批量导出 |

### 请求参数

```json
{
  "startDate": "2024-01-01",
  "endDate": "2024-12-31",
  "status": "completed",
  "format": "csv"
}
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

## 📊 影响范围

- {模块 A}：{影响说明}
- {模块 B}：{影响说明}
- 无数据库变更 / 有数据库变更（需 DBA 审核）

## ✅ 自测点

- [ ] 正常场景：{描述正常流程的测试结果}
- [ ] 边界场景：{描述边界条件测试结果}
- [ ] 异常场景：{描述异常情况测试结果}
- [ ] 规范检查：响应体格式、错误码、异常处理均符合 standard-api 规范

## ⚠️ 注意事项

- {需要 Review 重点关注的地方}
- {可能的风险点}
```

---

## 全流程检查清单

完成所有步骤后，逐项确认：

```
[ ] 步骤 1：需求已提炼并经用户确认
[ ] 步骤 2：已搜索代码库，理解现有逻辑
[ ] 步骤 3：代码符合 standard-api.cursorrules 规范
[ ] 步骤 4：Git 提交符合 git-commit.cursorrules 规范
[ ] 步骤 5：PR 描述已生成，包含背景、改动、影响、自测点
```

**全部通过后方可提测。**
