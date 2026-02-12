# Contributing to Claude SkillXfer

Thank you for your interest in contributing to Claude SkillXfer! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/GulshanArora7/Claude-SkillXfer.git
   cd Claude-SkillXfer
   ```
3. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. Install in development mode:
   ```bash
   pip install -e .
   ```
5. Verify installation:
   ```bash
   claude-skillxfer --help
   ```

## Adding Support for a New CLI

To add support for a new CLI adapter, follow these steps. You can also look at existing adapters (e.g., `cursor.py`, `gemini.py`) for reference:

1. **Create the adapter file** in `claude_skillxfer/cli_adapters/your_cli.py`:

```python
from pathlib import Path
from .base import CLIAdapter, SkillOutput

class YourCLIAdapter(CLIAdapter):
    @property
    def cli_name(self) -> str:
        return "your-cli"
    
    @property
    def default_install_path(self) -> Path:
        return Path.cwd() / ".your-cli" / "skills"
    
    @property
    def relative_install_path(self) -> Path:
        return Path(".your-cli") / "skills"
    
    def transform_skill_md(self, content: str, skill_name: str) -> str:
        # Transform SKILL.md for your CLI
        content = self._common_skill_md_transforms(content)
        # Add CLI-specific transformations
        return content
```

2. **Register the adapter** in `claude_skillxfer/cli_adapters/__init__.py`:

```python
from .your_cli import YourCLIAdapter

ADAPTERS = {
    # ... existing adapters
    'your-cli': YourCLIAdapter,
}
```

3. **Add detection** in `claude_skillxfer/cli.py`:

```python
def detect_installed_clis() -> List[str]:
    # ... existing detection
    if shutil.which("your-cli") or Path.home().joinpath(".your-cli").exists():
        detected.append("your-cli")
    return detected
```

4. **Test your adapter**:

```bash
claude-skillxfer --repo /path/to/desire/claude-skills-repo --cli your-cli --list-clis
claude-skillxfer --repo /path/to/desire/claude-skills-repo --cli your-cli --all --target /tmp/test
```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Add docstrings to all public functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

## Testing

Before submitting a PR, please test your changes:

1. **Repository structures**: Test with direct, nested, and hooks-based layouts
2. **Multiple skills**: Verify it works with several skills at once
3. **Output verification**: Check that the installed skill structure matches the expected format
4. **Path handling**: Test both default CLI paths and custom `--target` paths
5. **Error cases**: Test with invalid repositories, missing files, etc.

## Submitting Changes

1. Ensure your code follows the style guidelines and passes all tests
2. Write clear, descriptive commit messages (e.g., "Add support for NewCLI adapter")
3. Update documentation (README.md, CONTRIBUTING.md) if your changes affect user-facing features
4. Submit a pull request with:
   - A clear title describing the change
   - A detailed description of what was changed and why
   - Any relevant issue numbers

## Questions?

Feel free to open an issue or start a discussion if you have questions!
