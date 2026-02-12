"""
Cursor CLI adapter for Claude skills.

Cursor uses its own rules system with MDC (Markdown with metadata) format:
- Rules location: .cursor/rules/{name}.mdc
- Format: YAML frontmatter + markdown content
- Different from Agent Skills standard

This adapter transforms SKILL.md into Cursor's MDC rule format.
"""

from pathlib import Path
import re
import json

from .base import CLIAdapter, SkillOutput


class CursorAdapter(CLIAdapter):
    """
    Adapter for Cursor CLI/IDE.

    Cursor uses MDC (Markdown with metadata) format for rules.
    This adapter transforms skills into Cursor-compatible rules.
    """

    @property
    def cli_name(self) -> str:
        return "cursor"

    @property
    def default_install_path(self) -> Path:
        """
        Default to project-level .cursor/rules/ directory.

        Cursor checks:
        1. .cursor/rules/ (project rules - MDC format)
        2. Settings → Rules (global rules)
        """
        cwd = Path.cwd()
        return cwd / ".cursor" / "rules"

    @property
    def relative_install_path(self) -> Path:
        """Relative path structure for Cursor: .cursor/rules/"""
        return Path(".cursor") / "rules"

    @property
    def templates_dir_name(self) -> str:
        """Cursor uses 'assets' for additional files."""
        return "assets"

    @property
    def docs_dir_name(self) -> str:
        """Cursor uses 'references' for documentation."""
        return "references"

    def transform_skill_md(self, content: str, skill_name: str) -> str:
        """
        Transform SKILL.md into Cursor MDC rule format.

        MDC format requires:
        - YAML frontmatter with description, globs, alwaysApply
        - Markdown body with rule content
        """
        # Extract description from YAML frontmatter or content
        description = self._extract_description(content)

        # Determine file globs - extract from frontmatter or use generic default
        globs = self._get_skill_globs(content)

        # Apply common transformations
        content = self._common_skill_md_transforms(content)

        # Remove original YAML frontmatter (we'll add MDC frontmatter)
        content = self._strip_yaml_frontmatter(content)

        # Cursor MDC expects comma-separated globs (e.g. "**/*.py, **/*.ts"), not a JSON array
        try:
            glob_list = json.loads(globs) if isinstance(globs, str) else globs
            globs_for_mdc = ", ".join(glob_list) if glob_list else "**/*"
        except (json.JSONDecodeError, TypeError):
            globs_for_mdc = "**/*"

        # Build MDC format
        mdc_content = f"""---
description: {description}
globs: {globs_for_mdc}
alwaysApply: false
---

{content}

---

## Cursor Integration Notes

This rule was converted from a DevOps skill (SKILL.md format).

### Validation Scripts

Validation scripts are available in the `scripts/` directory.
Run them manually after editing files:

```bash
cd .cursor/rules/{skill_name}/scripts
python <script_name>.py [arguments]
```

### References

- Agent Skills standard: [agentskills.io](https://agentskills.io)
"""

        return mdc_content

    def _extract_description(self, content: str) -> str:
        """Extract description from YAML frontmatter or first paragraph."""
        # Try YAML frontmatter first
        yaml_match = re.search(
            r'^---\s*\n(.*?)\n---',
            content,
            re.DOTALL
        )
        if yaml_match:
            frontmatter = yaml_match.group(1)
            desc_match = re.search(
                r'description:\s*[>|]?\s*\n?\s*(.+?)(?:\n\w|\n---|\n\n)',
                frontmatter,
                re.DOTALL
            )
            if desc_match:
                desc = desc_match.group(1).strip()
                # Clean up multiline descriptions
                desc = ' '.join(desc.split())
                return desc[:200]  # Limit length

        # Fall back to first heading or paragraph
        heading_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()[:200]

        return "Claude skill"

    def _get_skill_globs(self, content: str) -> str:
        """Extract globs from SKILL.md frontmatter, or use default."""
        # Try to extract globs from YAML frontmatter
        yaml_match = re.search(
            r'^---\s*\n(.*?)\n---',
            content,
            re.DOTALL
        )
        if yaml_match:
            frontmatter = yaml_match.group(1)
            # Look for globs, files, or patterns in frontmatter
            glob_match = re.search(
                r'(?:globs|files|patterns):\s*(.+?)(?=\n\w|\n---|\n\n|$)',
                frontmatter,
                re.DOTALL | re.IGNORECASE
            )
            if glob_match:
                globs_str = glob_match.group(1).strip()
                # Handle YAML list format (e.g., "- **/*.py")
                if globs_str.startswith('-'):
                    items = re.findall(r'-\s*["\']?([^"\']+)["\']?', globs_str)
                    if items:
                        return json.dumps(items)
                # Handle JSON array format (e.g., '["**/*.py", "**/*.js"]' or ["**/*.py", "**/*.js"])
                elif globs_str.startswith('['):
                    try:
                        # Try parsing as-is
                        parsed = json.loads(globs_str)
                        if isinstance(parsed, list):
                            return json.dumps(parsed)
                    except (json.JSONDecodeError, ValueError):
                        # Try unquoting if it's a string representation
                        try:
                            unquoted = globs_str.strip("'\"")
                            parsed = json.loads(unquoted)
                            if isinstance(parsed, list):
                                return json.dumps(parsed)
                        except (json.JSONDecodeError, ValueError):
                            pass
                # Handle single quoted string containing JSON (e.g., '["**/*.py"]')
                elif (globs_str.startswith("'") and globs_str.endswith("'")) or \
                     (globs_str.startswith('"') and globs_str.endswith('"')):
                    try:
                        unquoted = globs_str.strip("'\"")
                        parsed = json.loads(unquoted)
                        if isinstance(parsed, list):
                            return json.dumps(parsed)
                    except (json.JSONDecodeError, ValueError):
                        pass
        
        # Default: truly generic glob that matches all files
        return '["**/*"]'

    def _strip_yaml_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter from content."""
        return re.sub(
            r'^---\s*\n.*?\n---\s*\n',
            '',
            content,
            flags=re.DOTALL
        )

    def transform_skill(self, source_dir: Path) -> SkillOutput:
        """
        Transform skill for Cursor.

        Creates MDC rule file and bundles supporting files.
        """
        skill_name = source_dir.name

        # Get base transformation
        output = super().transform_skill(source_dir)

        # Rename SKILL.md to {skill_name}.mdc for Cursor
        # The main rule file should be named after the skill
        output.cli_specific[f"{skill_name}.mdc"] = output.skill_md

        return output

    def write_output(self, output: SkillOutput, target_dir: Path) -> None:
        """
        Write transformed skill output to target directory.

        Single-level layout: target_dir is e.g. {name}/ with
        .mdc, scripts/, assets/, references/ directly inside (same as other CLIs).
        """
        target_dir.mkdir(parents=True, exist_ok=True)

        # Write the MDC rule file
        for rel_path, content in output.cli_specific.items():
            if rel_path.endswith('.mdc'):
                try:
                    (target_dir / rel_path).write_text(content, encoding='utf-8')
                except (PermissionError, OSError) as e:
                    raise OSError(f"Failed to write MDC file {rel_path}: {e}") from e
                break

        # Write supporting files directly under target_dir (no extra skill_name subdir)
        if output.scripts:
            scripts_dir = target_dir / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            for rel_path, content in output.scripts.items():
                try:
                    file_path = scripts_dir / rel_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding='utf-8')
                except (PermissionError, OSError) as e:
                    raise OSError(f"Failed to write script {rel_path}: {e}") from e

        if output.templates:
            templates_dir = target_dir / self.templates_dir_name
            templates_dir.mkdir(parents=True, exist_ok=True)
            for rel_path, content in output.templates.items():
                try:
                    file_path = templates_dir / rel_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding='utf-8')
                except (PermissionError, OSError) as e:
                    raise OSError(f"Failed to write template {rel_path}: {e}") from e

        if output.docs:
            docs_dir = target_dir / self.docs_dir_name
            docs_dir.mkdir(parents=True, exist_ok=True)
            for rel_path, content in output.docs.items():
                try:
                    file_path = docs_dir / rel_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding='utf-8')
                except (PermissionError, OSError) as e:
                    raise OSError(f"Failed to write doc {rel_path}: {e}") from e

        if output.examples:
            examples_dir = target_dir / "examples"
            examples_dir.mkdir(parents=True, exist_ok=True)
            for rel_path, content in output.examples.items():
                try:
                    file_path = examples_dir / rel_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding='utf-8')
                except (PermissionError, OSError) as e:
                    raise OSError(f"Failed to write example {rel_path}: {e}") from e
