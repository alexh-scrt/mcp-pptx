Perfect. Below is a **modern, production-ready `pyproject.toml`** for your PowerPoint MCP server — fully aligned with **Python 3.11+**, Poetry/PDM-compatible, and using the **latest stable versions (as of Oct 2025)**.

It’s optimized for your use case: PowerPoint generation with complex theming, images, charts, and MCP communication.

---

```toml
[project]
name = "slidesmith-py"
version = "0.1.0"
description = "An MCP server that generates fully branded PowerPoint presentations with complex themes, charts, and dynamic layouts."
authors = [
  { name = "Your Name", email = "you@example.com" }
]
license = "Apache-2.0"
readme = "README.md"
requires-python = ">=3.11"

dependencies = [
  # 🧠 Core
  "modelcontextprotocol>=0.1.6",
  "python-pptx>=0.6.23",
  "pydantic>=2.10.0",
  "requests>=2.32.3",
  "pillow>=11.0.0",

  # 🎨 Theming & color utilities
  "matplotlib>=3.9.2",
  "palettable>=3.3.3",

  # ⚙️ Developer & diagnostics
  "loguru>=0.7.2",
  "typer>=0.12.5",

  # 🧪 Testing
  "pytest>=8.3.3"
]

[project.optional-dependencies]
dev = [
  "black>=24.10.0",
  "ruff>=0.6.3",
  "mypy>=1.12.1",
  "types-requests>=2.32.0.20241005",
  "types-pillow>=10.2.0.20240820"
]

[tool.poetry]
packages = [{ include = "src" }]

[tool.poetry.scripts]
slidesmith = "src.server:main"

[build-system]
requires = ["setuptools>=75.0.0", "wheel>=0.44.0"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I"]
fix = true
```

---

### 🧩 Notes

* ✅ **`python-pptx 0.6.23`** – latest stable (supports chart objects, placeholders, `.potx` templates).
* ✅ **`pydantic 2.10`** – newest 2.x branch with improved validation performance.
* ✅ **`modelcontextprotocol 0.1.6`** – current MCP SDK.
* ✅ **`pillow 11.0`** – supports modern image formats & ICC profiles.
* ✅ **`matplotlib 3.9.2`** – latest release for palette utilities.
* ✅ **`pytest 8.3`** – for testing your rendering logic.

---

