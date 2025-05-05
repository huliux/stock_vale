# 重要文件位置（请勿修改）

为了项目的安全性和稳定性，请指示 Cline **不要读取或修改** 以下文件或目录：

- **环境变量文件**: `.env` 或包含敏感密钥的配置文件（如 `config.ini`，如果它包含密钥并且未被版本控制）。
- **虚拟环境目录**: 通常是 `venv/`, `.venv/`, `env/` 或类似名称。
- **构建/分发目录**: 通常是 `dist/`, `build/`, `*.egg-info/`。
- **Python 缓存文件**: `__pycache__/` 目录以及 `.pyc`, `.pyo` 文件。
- **包管理器的锁文件**: `Pipfile.lock` (pipenv), `poetry.lock` (poetry) 等（如果项目使用这些工具）。
- **Git 忽略文件**: `.gitignore`。
- **Pre-commit 配置文件**: `.pre-commit-config.yaml` (如果使用)。

请确保 Cline 在执行任何操作时都遵守这些限制，以防止意外修改或暴露敏感信息。
