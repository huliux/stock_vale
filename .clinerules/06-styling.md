# 样式指南 (stock_vale 项目 - 前端)

## 简要概述
本文档定义了 `stock_vale` 项目前端界面开发时推荐的样式指南，主要基于 Tailwind CSS。

## 核心原则
- **Tailwind CSS 优先**: 在编写组件样式时，**始终优先使用 Tailwind CSS 的工具类**直接在 JSX 中进行样式化。这有助于保持一致性并利用框架的优势。
- **配置文件驱动**:
    - 任何对 Tailwind CSS 的自定义（例如，添加新的颜色、字体、间距、断点）都应该在 `tailwind.config.ts` (或 `.js`) 文件中进行。避免在 CSS 文件中随意覆盖或添加与 Tailwind 配置冲突的样式。
    - 参考 `tailwind.config.ts` 来了解项目中可用的设计令牌（design tokens）。
- **响应式设计**:
    - 在设计页面和组件时，必须考虑**响应式设计**。
    - 优先使用 Tailwind CSS 的响应式前缀 (例如，`sm:`, `md:`, `lg:`, `xl:`, `2xl:`) 来适配不同的屏幕尺寸。
    - 采用移动优先 (Mobile-First) 的方法通常是推荐的。
- **组件化样式**:
    - 样式应尽可能与组件封装在一起。对于可重用组件，其样式应通过 props 或 Tailwind 类传递。
    - 避免创建大量全局 CSS 规则，除非是真正全局性的基础样式（通常在 `globals.css` 中通过 `@layer base` 定义）。
- **自定义 CSS 的使用**:
    - 仅在 Tailwind 无法直接实现所需样式，或者需要非常复杂的选择器或动画时，才考虑编写自定义 CSS。
    - 如果需要自定义 CSS，优先考虑在 `globals.css` 中使用 Tailwind 的 **`@layer components`** 或 **`@layer utilities`** 指令来组织它们，或者使用 CSS Modules。
    - 避免使用 `@apply` 来组合大量 Tailwind 类，这可能导致 CSS 文件膨胀并失去 Tailwind 的一些优势。优先考虑提取可重用组件。
- **可维护性与可读性**:
    - 保持 JSX 中的 Tailwind 类名列表简洁有序。考虑使用 `clsx` 或 `tailwind-merge` 等库来帮助管理条件类名。
    - 对于复杂的样式组合，可以考虑将其提取为组件变体或独立的组件。

## 颜色使用
- 优先使用 `tailwind.config.ts` 中定义的颜色名称（例如 `bg-primary`, `text-secondary`）。
- 避免直接使用十六进制颜色代码，除非是特殊情况。

## 间距
- 使用 Tailwind 的间距工具类（`p-`, `m-`, `space-x-`, `gap-` 等）来控制布局和元素间距。
- 保持一致的间距规范。
