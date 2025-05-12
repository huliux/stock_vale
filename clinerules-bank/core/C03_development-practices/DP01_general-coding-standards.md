# 通用编码标准指南

本文档旨在提供一套通用的编码标准和最佳实践，以促进代码的可读性、可维护性、一致性和整体质量。这些标准适用于多种编程语言，具体语言的特定规范（如 PEP 8 for Python）应作为本指南的补充。

## 1. 可读性与清晰性 (Readability and Clarity)

*   **有意义的命名 (Meaningful Names):**
    *   变量、函数、类、模块等应使用清晰、描述性强且无歧义的名称。
    *   名称应能准确反映其用途或所代表的实体。
    *   遵循特定语言的命名约定（如 Python 的 `snake_case` 用于函数/变量，`PascalCase` 用于类）。
*   **代码格式化 (Consistent Formatting):**
    *   采用统一的代码格式化风格（缩进、空格、换行等）。
    *   强烈推荐使用自动化格式化工具（如 Prettier for JS/TS, Black for Python, Spotless for Java/Kotlin）。
*   **代码结构与组织 (Structure and Organization):**
    *   **模块化：** 将代码组织成逻辑上独立的模块或文件，每个模块关注特定功能。
    *   **函数/方法长度：** 保持函数和方法简短、聚焦，每个只做一件事情（单一职责原则）。
    *   **避免深度嵌套：** 过深的条件或循环嵌套会降低可读性。考虑使用卫语句 (guard clauses)、提取方法等方式简化。
*   **注释 (Comments):**
    *   **解释“为什么”而非“是什么”：** 代码本身应清晰地表达其功能（“是什么”）。注释应用于解释复杂的逻辑、设计决策、或代码无法直接表达的意图（“为什么”）。
    *   **文档字符串 (Docstrings):** 为公共 API（模块、类、函数、方法）编写文档字符串，描述其用途、参数、返回值和可能的异常。遵循语言特定的文档字符串格式（如 Python PEP 257, Javadoc, KDoc）。
    *   **避免冗余注释：** 不要注释显而易见的代码。
    *   **及时更新：** 修改代码时，务必同步更新相关注释。
*   **魔法数字/字符串 (Magic Numbers/Strings):**
    *   避免在代码中直接使用未解释的字面量（“魔法数字”或“魔法字符串”）。
    *   应将它们定义为有意义的常量或枚举。

## 2. 代码质量与维护性 (Code Quality and Maintainability)

*   **不要重复自己 (DRY - Don't Repeat Yourself):**
    *   通过函数、类、模块、配置等方式抽象和重用通用逻辑，避免代码重复。
*   **单一职责原则 (SRP - Single Responsibility Principle):**
    *   每个模块、类或函数应专注于单一职责。
*   **开闭原则 (OCP - Open/Closed Principle):**
    *   代码应易于扩展（添加新功能），但难于修改（避免改动现有稳定代码）。
*   **代码简洁性 (Simplicity - KISS Principle):**
    *   优先选择简单直接的解决方案，避免不必要的复杂性。
*   **避免副作用 (Minimize Side Effects):**
    *   函数应尽可能纯粹，即对于相同的输入总是返回相同的输出，并且不修改外部状态。如果必须有副作用，应明确记录。
*   **错误处理：**
    *   参见 `DP02_error-handling-strategies.md`。
*   **配置管理：**
    *   参见 `DP03_configuration-management-best-practices.md`。

## 3. 特定语言的补充规范

*   **Python:**
    *   **PEP 8:** 严格遵循 [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)。
    *   **类型注解 (Type Hints):** 强烈推荐为函数参数和返回值添加类型注解 (PEP 484)。
        *   （例如：在Python项目中，类型提示有助于静态分析、提高代码可维护性并改善IDE支持。）
    *   **Linters/Formatters:** 使用 `Black` 进行代码格式化，`Flake8` (或 `Pylint`, `Ruff`) 进行代码风格和错误检查。推荐使用 `pre-commit` 钩子。
        *   （例如：在Python项目中，通常会配置代码格式化工具如Black和静态检查工具如Flake8/Pylint/Ruff，并通过`pre-commit`钩子在提交前自动执行。）
    *   **金融计算:** 涉及精确计算时，使用 `decimal.Decimal` 代替 `float`。
        *   （例如：在需要高精度计算的领域，如金融或科学计算，应使用特定于语言的高精度数据类型，如Python的`decimal.Decimal`，以避免浮点数舍入误差。）
*   **JavaScript/TypeScript:**
    *   **ESLint/Prettier:** 使用 ESLint 进行代码质量检查，Prettier 进行代码格式化。
    *   **TypeScript:** 充分利用类型系统，避免使用 `any` 类型。
    *   **命名约定:** 通常 `camelCase` 用于变量/函数，`PascalCase` 用于类/组件/类型。

## 4. 代码审查中的关注点

*   代码是否符合上述编码标准？
*   逻辑是否清晰、正确？
*   是否存在潜在的 Bug 或性能问题？
*   测试是否充分？
*   文档和注释是否到位？

---

本指南提供的是通用的编码标准。具体项目或团队可以根据自身情况和所用技术栈，在本指南基础上进行补充和细化。
