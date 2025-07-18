# MemoryBank-MCP-Server

一个集中的、事务性的上下文管理服务，旨在替代基于文件的脆弱状态管理系统。该服务将作为所有AI Agent的“单一事实来源(Single Source of Truth)”，管理任务、状态、日志和项目规范。

## 核心理念

*   **抽象化 (Abstraction):** Agent不应关心状态存储的具体形式，只与定义好的“记忆”工具交互。
*   **原子性 (Atomicity):** 关键操作（如“开始一个任务”）是事务性的，确保系统状态的一致性。
*   **集中化 (Centralization):** 所有与任务状态和项目上下文相关的数据都由本服务统一管理。
*   **服务化 (Service-Oriented):** 将流程封装成服务（API调用），使Agent的决策过程更简单。

## 架构

```mermaid
graph TD
    subgraph AI Agents
        A[AI Agent Core Engine]
    end

    subgraph "MemoryBank-MCP-Server (FastAPI)"
        direction LR
        B[API Endpoints <br> (MCP Tools)]
        C[Business Logic <br> (Service Layer)]
        D[Data Access Layer <br> (CRUD & ORM)]
    end

    subgraph "Persistent Storage"
        E[SQLite Database]
    end

    A -- "MCP Call (e.g., startWorkOnTask)" --> B
    B -- "Calls" --> C
    C -- "Uses" --> D
    D -- "DB Transaction (ACID)" --> E
```

## 安装与运行

### 1. 安装依赖

项目使用Python 3.10+。首先，创建并激活一个虚拟环境，然后安装所需的库：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 运行服务器

使用Uvicorn来运行FastAPI应用：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*   `--reload` 参数将在代码变更时自动重启服务器，非常适合开发环境。
*   服务器启动后，将在 `http://127.0.0.1:8000` 上可用。
*   交互式API文档 (Swagger UI) 位于 `http://127.0.0.1:8000/docs`。

## 测试

### 1. 运行单元测试

我们使用 `pytest` 进行单元测试，特别是为了验证核心事务操作的原子性。

```bash
pytest
```

### 2. 运行端到端测试

项目包含一个 `mcp_client.py` 脚本，用于模拟一个完整的任务生命周期，以进行端到端测试。

**确保服务器正在运行**，然后在另一个终端中执行：

```bash
# (可选) 在每次运行前清理数据库，以确保测试环境纯净
rm -f memorybank.db

# 运行客户端
python mcp_client.py
```

## API 端点 (MCP 工具)

以下是服务暴露的主要工具列表：

*   `/tools/createTaskChain`: 创建一个或多个有依赖关系的任务。
*   `/tools/getNextReadyTask`: 获取下一个可以执行的任务。
*   `/tools/getTaskDetails`: 获取指定任务的完整信息。
*   `/tools/startWorkOnTask`: **原子操作**。声明开始处理一个任务（更新状态为 `RUNNING` 并记录日志）。
*   `/tools/finishWorkOnTask`: **原子操作**。声明成功完成一个任务（更新状态为 `COMPLETED` 并记录日志）。
*   `/tools/updateTaskStatus`: 更新任务的状态，并能选择性地附加上下文信息。
*   `/tools/getSystemPatterns`: 获取系统的编码规范。
*   `/tools/updateSystemPatterns`: 更新系统的编码规范。
*   `/tools/getActiveContext`: 获取动态上下文。
*   `/tools/appendActiveContext`: 追加动态上下文。
