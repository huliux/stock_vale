# FastAPI 特定使用指南

本文档为使用 FastAPI 构建 Python Web API 时提供特定的指导原则和最佳实践。它旨在补充 `core/` 目录下的通用 API 设计指南 (`DA02_api-design-guidelines.md`) 和 Python 编码标准 (`DP01_general-coding-standards.md`)。

## 1. 项目结构建议 (FastAPI 应用)

*   **应用入口:**
    *   通常在项目根目录或 `app/` (或 `api/`) 子目录下的 `main.py` (或 `app.py`) 中创建 FastAPI 应用实例 (`app = FastAPI()`)。
*   **路由组织 (Routers):**
    *   对于中大型应用，使用 `APIRouter` 将不同业务模块的路由组织到独立的 Python 文件中（通常放在 `routers/` 或 `endpoints/` 目录下）。
    *   在主应用文件中使用 `app.include_router()` 包含这些子路由。
*   **模型定义 (Pydantic Models):**
    *   将所有 Pydantic 请求/响应模型、以及内部数据模型（如果也用 Pydantic）集中存放在一个或多个文件中（如 `models.py`, `schemas.py`，或按领域划分的 `models/user_models.py`）。
*   **服务层/业务逻辑 (Service Layer / Business Logic):**
    *   将核心业务逻辑从路由处理函数中分离出来，放到独立的服务模块或类中（如 `services.py` 或 `services/` 目录）。
    *   路由处理函数负责接收请求、调用服务层处理业务、并返回响应。
*   **依赖项/工具函数 (Dependencies / Utility Functions):**
    *   可重用的依赖项（如数据库连接、认证逻辑）和工具函数可以放在 `dependencies.py` 或 `utils.py` (或 `utils/` 目录) 中。
*   **配置 (Configuration):**
    *   应用配置（如数据库 URL、外部服务地址）应通过环境变量加载（参考 `DP05_configuration-management-best-practices.md`）。可以创建一个 `config.py` 来加载和提供配置。

## 2. Pydantic 模型使用要点

*   **请求与响应模型：** 明确为每个端点定义请求体和响应体的 Pydantic 模型。这能提供自动数据验证、序列化和 OpenAPI 文档生成。
*   **类型注解：** 严格使用 Python 类型注解。
*   **字段验证与默认值：** 利用 `Field` 从 Pydantic 导入，进行更细致的字段验证（如 `gt`, `le`, `min_length`, `regex`）和设置默认值。
    ```python
    from pydantic import BaseModel, Field
    from typing import Optional

    class Item(BaseModel):
        name: str = Field(..., min_length=3, description="The name of the item.")
        price: float = Field(..., gt=0, description="The price must be greater than zero.")
        description: Optional[str] = None
        tax: Optional[float] = Field(default=0.1, ge=0)
    ```
*   **嵌套模型：** 对于复杂的数据结构，使用嵌套的 Pydantic 模型。
*   **`Config` 子类：** 使用内部 `Config` 类来自定义 Pydantic 模型的行为，如 `orm_mode = True` (用于 SQLAlchemy 等 ORM 集成) 或 `alias_generator` (用于字段别名)。

## 3. 依赖注入 (Dependency Injection - DI)

*   FastAPI 的依赖注入系统非常强大，应充分利用：
    *   **函数作为依赖项：** 将可重用的逻辑（如获取当前用户、数据库会话管理）封装成函数，并通过 `Depends` 注入到路径操作函数中。
    *   **类作为依赖项：** 可以将类实例作为依赖项。
    *   **全局依赖项：** 为整个应用或特定路由器配置全局依赖项。
*   **优点：** 代码复用、逻辑分离、易于测试（可以替换依赖项的 mock 实现）。

## 4. 异步编程 (`async` / `await`)

*   **充分利用异步：** 对于 I/O 密集型操作（如数据库查询、外部 API 调用），应使用 `async def` 定义路径操作函数和依赖项，并在内部使用 `await` 调用异步库。
*   **异步库选择：** 确保使用的数据库驱动、HTTP 客户端等支持异步操作（如 `asyncpg` for PostgreSQL, `httpx` for HTTP requests）。
*   **避免阻塞操作：** 在异步函数中避免执行长时间的同步阻塞操作，这会影响应用的并发性能。如果必须执行，考虑使用 `run_in_threadpool`。

## 5. 错误处理

*   **HTTPException：** 使用 FastAPI 的 `HTTPException` 来返回标准的 HTTP 错误响应。
*   **自定义异常处理器：** 使用 `@app.exception_handler(CustomException)` 装饰器为自定义异常类型注册处理器，以返回统一的错误响应格式。
*   **请求验证错误：** FastAPI 会自动处理 Pydantic 模型的验证错误，并返回 `422 Unprocessable Entity` 响应。

## 6. 测试 FastAPI 应用

*   **`TestClient`：** FastAPI 提供了 `TestClient`，用于在测试中直接调用应用，而无需启动实际的 HTTP 服务器。
*   **依赖覆盖 (Overriding Dependencies):** 在测试中，可以使用 `app.dependency_overrides` 来替换依赖项的实现（例如，用 mock 数据库会话替换真实数据库会话）。
    ```python
    from fastapi.testclient import TestClient
    from .main import app # 假设 app 在 main.py 中

    client = TestClient(app)

    def override_get_db():
        # 返回一个 mock 的数据库会话
        pass

    app.dependency_overrides[get_db] = override_get_db # get_db 是原始依赖

    def test_read_main():
        response = client.get("/")
        assert response.status_code == 200
    ```

## 7. OpenAPI 文档

*   FastAPI 会自动根据你的路径操作函数、Pydantic 模型和依赖项生成 OpenAPI 规范 (通常在 `/openapi.json`) 和交互式 API 文档界面 (Swagger UI 在 `/docs`, ReDoc 在 `/redoc`)。
*   通过在路径操作函数和 Pydantic 模型中添加 `description`, `summary`, `tags`, `response_model`, `status_code` 等参数，可以丰富生成的 OpenAPI 文档。

---

遵循这些 FastAPI 特定的指南，结合通用的 API 设计和 Python 编码原则，有助于构建高质量、可维护的 FastAPI 应用。
