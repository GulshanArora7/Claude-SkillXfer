"""
OpenCode CLI adapter for Claude skills.

OpenCode supports the Agent Skills standard and looks for skills in:
- .opencode/skill/{name}/ (project-level)
- .claude/skills/{name}/ (also supported)
- ~/.opencode/skill/{name}/ (global)
"""

from pathlib import Path

from .base import CLIAdapter, SkillOutput


class OpenCodeAdapter(CLIAdapter):
    """
    Adapter for OpenCode CLI.

    OpenCode natively supports the Agent Skills specification, so
    transformations are minimal.
    """

    @property
    def cli_name(self) -> str:
        return "opencode"

    @property
    def default_install_path(self) -> Path:
        """
        Default to project-level .opencode/skill/ directory.

        OpenCode checks multiple locations:
        1. .opencode/skill/ (project, preferred)
        2. .claude/skills/ (compatible with Claude Code)
        3. ~/.opencode/skill/ (global)
        """
        # Check if we're in a project with existing OpenCode config
        cwd = Path.cwd()
        opencode_path = cwd / ".opencode" / "skill"
        claude_path = cwd / ".claude" / "skills"

        # Prefer existing directory, otherwise default to .opencode/skill/
        if claude_path.exists():
            return claude_path
        return opencode_path

    @property
    def relative_install_path(self) -> Path:
        """Relative path structure for OpenCode: .opencode/skill/"""
        return Path(".opencode") / "skill"

    def transform_skill_md(self, content: str, skill_name: str) -> str:
        """
        Transform SKILL.md for OpenCode compatibility.

        OpenCode is highly compatible with Claude Code, so changes are minimal.
        """
        # Apply common transformations
        content = self._common_skill_md_transforms(content)

        # Add OpenCode-specific section at the end
        opencode_section = f"""

---

## OpenCode CLI Usage

This skill is compatible with OpenCode CLI. To use:

```bash
# The skill is automatically loaded when placed in .opencode/skill/{skill_name}/
# OpenCode will discover it and make it available in conversations.

# To manually invoke scripts:
cd .opencode/skill/{skill_name}/scripts
python <script_name>.py [arguments]
```

### Validation Scripts

The `scripts/` directory contains Python scripts that can be run
manually after editing files.

See `scripts/README.md` for detailed usage instructions.
"""

        # Only add if not already present
        if "## OpenCode CLI Usage" not in content:
            content += opencode_section

        return content
