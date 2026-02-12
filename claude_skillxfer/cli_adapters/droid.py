"""
Factory.ai Droid CLI adapter for Claude skills.

Droid CLI (v0.26.0+) natively supports Claude Code skills format:
- Skills location: .factory/skills/{name}/ or ~/.factory/skills/{name}/
- Uses standard Agent Skills format (SKILL.md + scripts/)
- Can also import from .claude/skills/ directory
"""

from pathlib import Path

from .base import CLIAdapter, SkillOutput


class DroidAdapter(CLIAdapter):
    """
    Adapter for Factory.ai Droid CLI.

    Droid CLI follows Claude Code's skill format closely.
    Skills are installed to .factory/skills/ by default.
    """

    @property
    def cli_name(self) -> str:
        return "droid"

    @property
    def default_install_path(self) -> Path:
        """
        Default to project-level .factory/skills/ directory.

        Droid CLI checks:
        1. .factory/skills/{name}/ (project scope)
        2. ~/.factory/skills/{name}/ (user scope)
        3. .claude/skills/{name}/ (Claude Code compatibility)
        """
        cwd = Path.cwd()
        return cwd / ".factory" / "skills"

    @property
    def relative_install_path(self) -> Path:
        """Relative path structure for Droid: .factory/skills/"""
        return Path(".factory") / "skills"

    def transform_skill_md(self, content: str, skill_name: str) -> str:
        """
        Transform SKILL.md for Droid CLI compatibility.

        Droid CLI is highly compatible with Claude Code, so
        minimal transformation is needed.
        """
        # Apply common transformations
        content = self._common_skill_md_transforms(content)

        # Add Droid-specific section
        droid_section = f"""

---

## Droid CLI Usage

This skill is compatible with Factory.ai Droid CLI (v0.26.0+). To use:

```bash
# Skills are auto-discovered from .factory/skills/{skill_name}/
# Use the /skills command to manage skills

# To run scripts manually:
cd .factory/skills/{skill_name}/scripts
python <script_name>.py [arguments]
```

### Features

Droid CLI with this skill provides:
- Claude Code skills compatibility
- Auto-discovery from .claude/skills/ directory
- Self-healing and auto-debugging capabilities
- Custom Droids for specialized workflows

### Enabling Skills

Ensure Custom Droids are enabled:
```bash
# Via settings
/settings → Experimental → Custom Droids

# Or add to ~/.factory/settings.json
{{"enableCustomDroids": true}}
```

See `scripts/README.md` for script usage.
"""

        # Only add if not already present
        if "## Droid CLI Usage" not in content:
            content += droid_section

        return content
