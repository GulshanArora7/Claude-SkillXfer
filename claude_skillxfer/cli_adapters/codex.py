"""
OpenAI Codex CLI adapter for Claude skills.

Codex CLI follows the Agent Skills standard with some naming conventions:
- Skills location: .codex/skills/{name}/
- templates/ → assets/ (Codex convention)
- docs/ → references/ (Codex convention)
"""

from pathlib import Path

from .base import CLIAdapter, SkillOutput


class CodexAdapter(CLIAdapter):
    """
    Adapter for OpenAI Codex CLI.

    Codex follows Agent Skills standard but uses different directory names:
    - assets/ instead of templates/
    - references/ instead of docs/
    """

    @property
    def cli_name(self) -> str:
        return "codex"

    @property
    def default_install_path(self) -> Path:
        """
        Default to project-level .codex/skills/ directory.

        Codex CLI checks:
        1. .codex/skills/{name}/ (repository scope)
        2. ~/.codex/skills/{name}/ (user scope)
        """
        cwd = Path.cwd()
        return cwd / ".codex" / "skills"

    @property
    def relative_install_path(self) -> Path:
        """Relative path structure for Codex: .codex/skills/"""
        return Path(".codex") / "skills"

    @property
    def templates_dir_name(self) -> str:
        """Codex uses 'assets' instead of 'templates'."""
        return "assets"

    @property
    def docs_dir_name(self) -> str:
        """Codex uses 'references' instead of 'docs'."""
        return "references"

    def transform_skill_md(self, content: str, skill_name: str) -> str:
        """
        Transform SKILL.md for Codex CLI compatibility.

        Changes:
        - Remove Claude Code-specific syntax
        - Update directory references (templates → assets, docs → references)
        - Add Codex-specific usage section
        """
        # Apply common transformations
        content = self._common_skill_md_transforms(content)

        # Update directory references
        content = content.replace("templates/", "assets/")
        content = content.replace("docs/", "references/")
        content = content.replace("`templates`", "`assets`")
        content = content.replace("`docs`", "`references`")

        # Add Codex-specific section
        codex_section = f"""

---

## Codex CLI Usage

This skill is compatible with OpenAI Codex CLI. To use:

```bash
# Enable skills in Codex
codex --enable skills

# The skill is automatically loaded from .codex/skills/{skill_name}/

# To run scripts manually:
cd .codex/skills/{skill_name}/scripts
python <script_name>.py [arguments]
```

### Directory Structure

Codex CLI uses slightly different directory names:
- `assets/` - Code templates (called `templates/` in Claude Code)
- `references/` - Documentation (called `docs/` in Claude Code)
- `scripts/` - Automation scripts

See `scripts/README.md` for script usage.
"""

        # Only add if not already present
        if "## Codex CLI Usage" not in content:
            content += codex_section

        return content
