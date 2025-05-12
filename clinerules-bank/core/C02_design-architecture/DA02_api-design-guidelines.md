# 通用 API 设计指南

本文档提供了设计和实现应用程序编程接口 (API) 的通用指导原则和最佳实践，旨在创建易于理解、使用、维护和演进的 API。

## 1. API 设计核心原则

*   **面向消费者 (Consumer-Oriented):**
    *   API 的设计应首先考虑其消费者的需求和使用场景。
    *   提供清晰、一致且符合直觉的接口。
*   **简单性 (Simplicity):**
    *   API 应尽可能简单，避免不必要的复杂性。
    *   易于学习和集成。
*   **一致性 (Consistency):**
    *   在整个 API 中保持命名约定、数据格式、错误处理方式等的一致性。
    *   这有助于降低学习曲线，减少使用者的困惑。
*   **可发现性 (Discoverability):**
    *   API 应易于被发现和理解其功能。
    *   提供良好的文档（如 OpenAPI/Swagger 规范）和自描述性资源。
*   **灵活性与可扩展性 (Flexibility and Extensibility):**
    *   API 设计应考虑到未来的需求变化和功能扩展。
    *   采用版本控制等策略来管理演进。
*   **可靠性与性能 (Reliability and Performance):**
    *   API 应稳定可靠，并能在可接受的时间内响应。
    *   考虑缓存、限流、异步处理等机制。
*   **安全性 (Security):**
    *   API 必须从设计之初就考虑安全性，包括认证、授权、输入验证、数据保护等。

## 2. RESTful API 设计实践 (常用作 HTTP API 指南)

虽然 API 可以有多种风格 (如 GraphQL, gRPC)，RESTful 风格由于其简洁性和基于 HTTP 标准的特性而被广泛应用于 Web API。

*   **使用名词表示资源 (Use Nouns for Resources):**
    *   API 端点应使用名词（通常是复数形式）来表示资源。
    *   例如：`/users`, `/products`, `/orders`。
    *   *(例如：一个金融服务 API 可能使用 /api/v1/valuations 来表示估值资源集合。)*
*   **使用 HTTP 方法表示操作 (Use HTTP Methods for Operations):**
    *   `GET`: 读取资源。
    *   `POST`: 创建新资源。
    *   `PUT`: 完整更新现有资源（替换）。
    *   `PATCH`: 部分更新现有资源。
    *   `DELETE`: 删除资源。
*   **恰当使用 HTTP 状态码 (Use HTTP Status Codes Appropriately):**
    *   `2xx` (成功): 如 `200 OK`, `201 Created`, `204 No Content`。
    *   `3xx` (重定向): 如 `301 Moved Permanently`。
    *   `4xx` (客户端错误): 如 `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `422 Unprocessable Entity` (用于验证错误)。
    *   `5xx` (服务器错误): 如 `500 Internal Server Error`, `503 Service Unavailable`。
*   **版本控制 (Versioning):**
    *   当 API 发生不兼容的变更时，应引入新版本以避免破坏现有客户端。
    *   常见方式：URL路径中加入版本号 (如 `/api/v1/users`, `/api/v2/users`)。
*   **请求与响应体格式 (Request and Response Body Format):**
    *   通常使用 JSON 作为数据交换格式。
    *   请求体和响应体应结构清晰，字段命名一致。
    *   *(例如：在 Python 后端，可以使用 Pydantic 或 dataclasses 来定义 JSON 请求和响应的数据模型。)*
*   **过滤、排序与分页 (Filtering, Sorting, and Pagination):**
    *   对于返回资源集合的 API，应提供查询参数来实现过滤、排序和分页功能。
    *   例如：`GET /users?status=active&sort_by=lastName&page=2&limit=20`。
*   **错误处理 (Error Handling):**
    *   提供统一、结构化的错误响应格式，包含有用的错误信息（如错误代码、错误描述、有时可包含错误详情）。
    *   避免在错误响应中泄露敏感信息。
*   **数据验证 (Data Validation):**
    *   对所有客户端输入进行严格验证。
    *   使用如 Pydantic (Python) 或 Joi (JavaScript) 等库在服务器端强制执行数据模式和约束。
    *   *(例如：许多现代 Web 框架（如 FastAPI 结合 Pydantic）能基于数据模型自动进行请求数据验证。)*
*   **安全性考虑 (Security Considerations):**
    *   **认证 (Authentication):** 验证请求者的身份（如 API Key, OAuth 2.0, JWT）。
    *   **授权 (Authorization):** 确认已认证的请求者是否有权访问特定资源或执行特定操作。
    *   **HTTPS:** 始终使用 HTTPS 加密 API 通信。
    *   **输入清理与参数化查询:** 防止注入攻击 (如 SQL 注入, XSS)。

## 3. API 文档化

*   **OpenAPI (Swagger) 规范:**
    *   使用 OpenAPI 规范来描述 API 的端点、参数、请求/响应模型、认证方式等。
    *   许多框架（如 FastAPI）可以自动生成 OpenAPI 规范。
    *   生成的规范可以用于生成客户端代码、API 文档站点 (如 Swagger UI, ReDoc)。
*   **文档内容：**
    *   除了规范本身，还应提供概述、认证指南、使用示例、错误代码解释等。

---

本指南提供的是通用的 API 设计原则和实践。具体项目的 API 设计应根据其业务需求、技术栈和目标用户进行调整和细化。
