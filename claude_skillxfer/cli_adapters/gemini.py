"""
Google Gemini CLI adapter for Claude skills.

Gemini CLI supports Agent Skills via the skillz MCP server extension:
- Skills location: ~/.gemini/skills/{name}/
- Uses standard Agent Skills format (SKILL.md + scripts/)
- Can share skills with Claude Code (no copying needed)
"""

from pathlib import Path

from .base import CLIAdapter, SkillOutput


class GeminiAdapter(CLIAdapter):
    """
    Adapter for Google Gemini CLI.

    Gemini CLI follows the Agent Skills standard closely.
    Skills are installed to ~/.gemini/skills/ by default.
    """

    @property
    def cli_name(self) -> str:
        return "gemini"

    @property
    def default_install_path(self) -> Path:
        """
        Default to user-level ~/.gemini/skills/ directory.

        Gemini CLI looks for skills in:
        1. ~/.gemini/skills/{name}/ (user scope)
        2. Can also share with Claude Code's .claude/skills/
        """
        return Path.home() / ".gemini" / "skills"

    @property
    def relative_install_path(self) -> Path:
        """Relative path structure for Gemini: .gemini/skills/"""
        return Path(".gemini") / "skills"

    def transform_skill_md(self, content: str, skill_name: str) -> str:
        """
        Transform SKILL.md for Gemini CLI compatibility.

        Gemini CLI is highly compatible with Agent Skills standard,
        so minimal transformation is needed.
        """
        # Apply common transformations
        content = self._common_skill_md_transforms(content)

        # Add Gemini-specific section
        gemini_section = f"""

---

## Gemini CLI Usage

This skill is compatible with Google Gemini CLI. To use:

```bash
# Skills are installed to ~/.gemini/skills/{skill_name}/
# Gemini CLI automatically discovers and loads them.

# Restart Gemini CLI to load new skills
gemini

# To run scripts manually:
cd ~/.gemini/skills/{skill_name}/scripts
python <script_name>.py [arguments]
```

### Features

Gemini CLI with this skill provides:
- Automatic skill discovery from ~/.gemini/skills/
- 1M+ token context window (Gemini 2.5 Pro)
- Built-in Google Search grounding
- MCP extensibility

### Shared Skills

You can share skills between Gemini CLI and Claude Code by symlinking:

```bash
ln -s ~/.gemini/skills/{skill_name} ~/.claude/skills/{skill_name}
```

See `scripts/README.md` for script usage.
"""

        # Only add if not already present
        if "## Gemini CLI Usage" not in content:
            content += gemini_section

        return content
