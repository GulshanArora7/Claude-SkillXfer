"""
Google Antigravity adapter for Claude skills.

Antigravity uses the Agent Skills standard:
- Workspace: .agent/skills/{name}/
- Global: ~/.gemini/antigravity/skills/{name}/
- Structure: SKILL.md, scripts/, examples/, resources/
"""

from pathlib import Path

from .base import CLIAdapter, SkillOutput


class AntigravityAdapter(CLIAdapter):
    """
    Adapter for Google Antigravity.

    Skills go to .agent/skills/ (workspace) with SKILL.md, scripts/,
    examples/, and resources/ (templates + references).
    """

    @property
    def cli_name(self) -> str:
        return "antigravity"

    @property
    def default_install_path(self) -> Path:
        """Workspace-level .agent/skills/ (project-specific)."""
        return Path.cwd() / ".agent" / "skills"

    @property
    def relative_install_path(self) -> Path:
        return Path(".agent") / "skills"

    def transform_skill_md(self, content: str, skill_name: str) -> str:
        """Apply common transforms; Antigravity uses standard SKILL.md."""
        content = self._common_skill_md_transforms(content)
        section = f"""

---

## Antigravity

This skill is in `.agent/skills/{skill_name}/`. Scripts: `scripts/`, assets: `resources/`.
"""
        if "## Antigravity" not in content:
            content += section
        return content

    def write_output(self, output: SkillOutput, target_dir: Path) -> None:
        """Write SKILL.md, scripts/, examples/, and resources/ (templates + references)."""
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            (target_dir / "SKILL.md").write_text(output.skill_md, encoding='utf-8')
        except (PermissionError, OSError) as e:
            raise OSError(f"Failed to write SKILL.md to {target_dir}: {e}") from e

        if output.scripts:
            scripts_dir = target_dir / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            for rel_path, content in output.scripts.items():
                try:
                    f = scripts_dir / rel_path
                    f.parent.mkdir(parents=True, exist_ok=True)
                    f.write_text(content, encoding='utf-8')
                except (PermissionError, OSError) as e:
                    raise OSError(f"Failed to write script {rel_path}: {e}") from e

        if output.templates or output.docs:
            resources_dir = target_dir / "resources"
            resources_dir.mkdir(exist_ok=True)
            if output.templates:
                templates_dir = resources_dir / "templates"
                templates_dir.mkdir(exist_ok=True)
                for rel_path, content in output.templates.items():
                    try:
                        f = templates_dir / rel_path
                        f.parent.mkdir(parents=True, exist_ok=True)
                        f.write_text(content, encoding='utf-8')
                    except (PermissionError, OSError) as e:
                        raise OSError(f"Failed to write template {rel_path}: {e}") from e
            if output.docs:
                refs_dir = resources_dir / "references"
                refs_dir.mkdir(exist_ok=True)
                for rel_path, content in output.docs.items():
                    try:
                        f = refs_dir / rel_path
                        f.parent.mkdir(parents=True, exist_ok=True)
                        f.write_text(content, encoding='utf-8')
                    except (PermissionError, OSError) as e:
                        raise OSError(f"Failed to write doc {rel_path}: {e}") from e

        if output.examples:
            examples_dir = target_dir / "examples"
            examples_dir.mkdir(exist_ok=True)
            for rel_path, content in output.examples.items():
                try:
                    f = examples_dir / rel_path
                    f.parent.mkdir(parents=True, exist_ok=True)
                    f.write_text(content, encoding='utf-8')
                except (PermissionError, OSError) as e:
                    raise OSError(f"Failed to write example {rel_path}: {e}") from e

        for rel_path, content in output.cli_specific.items():
            try:
                f = target_dir / rel_path
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(content, encoding='utf-8')
            except (PermissionError, OSError) as e:
                raise OSError(f"Failed to write CLI-specific file {rel_path}: {e}") from e
