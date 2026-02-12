"""
Base adapter interface for CLI-specific skill transformations.

All CLI adapters inherit from CLIAdapter and implement the transform_skill method
to convert Claude skills to their target CLI format.

This adapter automatically detects the repository structure to support different
Claude skills repository layouts:
- Direct structure: skill-name/SKILL.md, skill-name/scripts/
- Nested structure: skill-name/skills/SKILL.md, skill-name/skills/scripts/
- Hooks structure: skill-name/hooks/scripts/, skill-name/templates/
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
import re
import shutil


@dataclass
class SkillOutput:
    """Transformed skill output for a specific CLI."""

    skill_md: str                              # Transformed SKILL.md content
    scripts: Dict[str, str] = field(default_factory=dict)      # {filename: content}
    templates: Dict[str, str] = field(default_factory=dict)    # {filename: content}
    docs: Dict[str, str] = field(default_factory=dict)         # {filename: content}
    examples: Dict[str, str] = field(default_factory=dict)     # {filename: content}
    cli_specific: Dict[str, str] = field(default_factory=dict) # CLI-specific files


class CLIAdapter(ABC):
    """
    Abstract base class for CLI-specific skill transformations.

    Each adapter handles:
    1. Path resolution for the target CLI
    2. SKILL.md transformation (removing Claude Code-specific syntax)
    3. Script bundling (including shared modules)
    4. Directory structure mapping (templates → assets, etc.)
    """

    def __init__(self, repo_root: Path):
        """
        Initialize adapter with repository root.

        Args:
            repo_root: Path to Claude skills repository root
        """
        self.repo_root = repo_root
        self.shared_dir = repo_root / "shared"

    @property
    @abstractmethod
    def cli_name(self) -> str:
        """CLI identifier (e.g., 'opencode', 'codex', 'gemini')."""
        pass

    @property
    @abstractmethod
    def default_install_path(self) -> Path:
        """Default installation directory for this CLI."""
        pass

    @property
    def relative_install_path(self) -> Path:
        """
        Relative path structure for this CLI (e.g., .cursor/rules/ for Cursor).
        
        Used when --target is specified to create CLI structure under target directory.
        
        Returns:
            Relative Path (e.g., Path('.cursor/rules'))
        """
        # Default: use the default path relative to current directory
        # This can be overridden by adapters if needed
        # Note: All adapters should override this property to return a proper relative path
        try:
            if self.default_install_path.is_relative_to(Path.cwd()):
                return self.default_install_path.relative_to(Path.cwd())
        except (ValueError, AttributeError):
            # If is_relative_to is not available (Python < 3.9) or path is absolute
            pass
        # Fallback: return the path as-is (adapters should override this)
        return self.default_install_path

    @property
    def templates_dir_name(self) -> str:
        """Name of templates directory in output (can be overridden)."""
        return "templates"

    @property
    def docs_dir_name(self) -> str:
        """Name of docs directory in output (can be overridden)."""
        return "docs"

    def get_skill_install_name(self, skill_name: str) -> str:
        """
        Get the installation name for a skill.

        Args:
            skill_name: Original skill name

        Returns:
            Installation name (just the skill name, no prefix)
        """
        return skill_name

    @abstractmethod
    def transform_skill_md(self, content: str, skill_name: str) -> str:
        """
        Transform SKILL.md content for this CLI.

        Args:
            content: Original SKILL.md content
            skill_name: Name of the skill being transformed

        Returns:
            Transformed SKILL.md content
        """
        pass

    def transform_skill(self, source_dir: Path) -> SkillOutput:
        """
        Transform a skill for this CLI.

        Automatically detects the repository structure to support different layouts.

        Args:
            source_dir: Path to skill directory (e.g., {skill-name}/)

        Returns:
            SkillOutput with transformed files
        """
        skill_name = source_dir.name

        # Detect repository structure
        structure = self._detect_skill_structure(source_dir)

        # Read and transform SKILL.md
        skill_md_path = structure['skill_md']
        if skill_md_path.exists():
            try:
                skill_md = skill_md_path.read_text(encoding='utf-8')
                skill_md = self.transform_skill_md(skill_md, skill_name)
            except (UnicodeDecodeError, PermissionError, OSError) as e:
                # If we can't read SKILL.md, create a placeholder
                skill_md = f"# {skill_name}\n\nError reading SKILL.md: {e}"
        else:
            skill_md = f"# {skill_name}\n\nNo SKILL.md found in source."

        # Copy scripts from detected location
        scripts = self._copy_scripts_from_structure(source_dir, structure)

        # Generate scripts README
        scripts["README.md"] = self._generate_scripts_readme(source_dir, structure)

        # Copy templates/assets from detected locations
        templates = self._copy_templates_from_structure(source_dir, structure)

        # Copy docs/references from detected locations
        docs = self._copy_docs_from_structure(source_dir, structure)

        # Copy examples if they exist
        examples = self._copy_directory_contents(source_dir / "examples")
        # Also check in skills/ subdirectory
        if structure.get('skills_subdir'):
            examples.update(self._copy_directory_contents(structure['skills_subdir'] / "examples"))

        return SkillOutput(
            skill_md=skill_md,
            scripts=scripts,
            templates=templates,
            docs=docs,
            examples=examples,
        )

    def _detect_skill_structure(self, source_dir: Path) -> Dict[str, Path]:
        """
        Detect the structure of a skill directory.

        Supports multiple repository layouts:
        1. Direct: skill-name/SKILL.md, skill-name/scripts/
        2. Nested: skill-name/skills/SKILL.md, skill-name/skills/scripts/
        3. Hooks: skill-name/hooks/scripts/, skill-name/templates/

        Returns:
            Dict with detected paths for skill_md, scripts_dir, templates_dir, docs_dir
        """
        structure = {}

        # Check for nested structure (skills/ subdirectory)
        skills_subdir = source_dir / "skills"
        if skills_subdir.exists() and (skills_subdir / "SKILL.md").exists():
            structure['skills_subdir'] = skills_subdir
            structure['skill_md'] = skills_subdir / "SKILL.md"
            structure['scripts_dir'] = skills_subdir / "scripts"
            structure['templates_dir'] = skills_subdir / "templates"
            structure['docs_dir'] = skills_subdir / "docs"
            structure['assets_dir'] = skills_subdir / "assets"
        else:
            # Direct structure
            structure['skill_md'] = source_dir / "SKILL.md"
            structure['scripts_dir'] = source_dir / "scripts"
            structure['templates_dir'] = source_dir / "templates"
            structure['docs_dir'] = source_dir / "docs"
            structure['assets_dir'] = source_dir / "assets"

        # Check for hooks structure (hooks-based layout)
        hooks_dir = source_dir / "hooks"
        if hooks_dir.exists() and (hooks_dir / "scripts").exists():
            structure['hooks_dir'] = hooks_dir
            structure['scripts_dir'] = hooks_dir / "scripts"

        return structure

    def _copy_scripts_from_structure(self, source_dir: Path, structure: Dict[str, Path]) -> Dict[str, str]:
        """
        Copy scripts from the detected structure.

        Checks multiple possible locations:
        - hooks/scripts/ (hooks-based layout)
        - skills/scripts/ (nested structure)
        - scripts/ (direct structure)
        """
        scripts = {}

        # Try hooks/scripts/ first (hooks-based layout)
        if 'hooks_dir' in structure:
            scripts_dir = structure.get('hooks_dir') / "scripts"
            if scripts_dir.exists():
                scripts.update(self._copy_scripts_from_dir(scripts_dir))
                return scripts

        # Try detected scripts_dir
        scripts_dir = structure.get('scripts_dir')
        if scripts_dir and scripts_dir.exists():
            scripts.update(self._copy_scripts_from_dir(scripts_dir))

        return scripts

    def _copy_scripts_from_dir(self, scripts_dir: Path) -> Dict[str, str]:
        """Copy Python scripts from a directory."""
        scripts = {}

        for script_path in scripts_dir.rglob("*.py"):
            try:
                rel_path = script_path.relative_to(scripts_dir)
                content = script_path.read_text(encoding='utf-8')
                content = self._transform_script(content)
                scripts[str(rel_path)] = content
            except (UnicodeDecodeError, PermissionError, OSError):
                # Skip files that can't be read (binary, permission issues, etc.)
                continue

        # Also copy any JSON data files
        for json_path in scripts_dir.rglob("*.json"):
            try:
                rel_path = json_path.relative_to(scripts_dir)
                scripts[str(rel_path)] = json_path.read_text(encoding='utf-8')
            except (UnicodeDecodeError, PermissionError, OSError):
                # Skip files that can't be read
                continue

        return scripts

    def _copy_templates_from_structure(self, source_dir: Path, structure: Dict[str, Path]) -> Dict[str, str]:
        """
        Copy templates/assets from detected structure.

        Checks multiple locations, prioritizing structure-detected paths:
        - structure's assets_dir/templates/ (nested or direct)
        - structure's templates_dir/
        - root assets/templates/ (fallback)
        - root templates/ (fallback)
        """
        templates = {}

        # Prioritize structure's assets_dir/templates (works for both nested and direct)
        assets_dir = structure.get('assets_dir')
        if assets_dir and assets_dir.exists():
            assets_templates = assets_dir / "templates"
            if assets_templates.exists():
                templates.update(self._copy_directory_contents(assets_templates))

            # Copy other assets (excluding templates subdirectory to avoid duplicates)
            for file_path in assets_dir.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(assets_dir)
                    # Skip if already in templates
                    if str(rel_path).startswith("templates/"):
                        continue
                    try:
                        templates[str(rel_path)] = file_path.read_text(encoding='utf-8')
                    except UnicodeDecodeError:
                        pass

        # Try structure's templates_dir
        templates_dir = structure.get('templates_dir')
        if templates_dir and templates_dir.exists():
            templates.update(self._copy_directory_contents(templates_dir))

        # Fallback: check root assets/templates/ (for direct structure without structure detection)
        if not templates:  # Only if nothing found yet
            root_assets_templates = source_dir / "assets" / "templates"
            if root_assets_templates.exists():
                templates.update(self._copy_directory_contents(root_assets_templates))

            # Fallback: check root assets/ directory
            root_assets = source_dir / "assets"
            if root_assets.exists():
                for file_path in root_assets.rglob("*"):
                    if file_path.is_file():
                        rel_path = file_path.relative_to(root_assets)
                        # Skip if already in templates
                        if str(rel_path).startswith("templates/"):
                            continue
                        try:
                            templates[str(rel_path)] = file_path.read_text(encoding='utf-8')
                        except UnicodeDecodeError:
                            pass

        return templates

    def _copy_docs_from_structure(self, source_dir: Path, structure: Dict[str, Path]) -> Dict[str, str]:
        """
        Copy docs/references from detected structure.

        Checks multiple locations:
        - references/ (references directory style)
        - docs/ (docs directory style)
        - skills/references/ (nested structure)
        - skills/docs/ (nested structure)
        """
        docs = {}

        # Try references/ first (references directory style)
        references_dir = source_dir / "references"
        if references_dir.exists():
            docs.update(self._copy_directory_contents(references_dir))

        # Try docs/ (docs directory style)
        docs_dir = structure.get('docs_dir')
        if docs_dir and docs_dir.exists():
            docs.update(self._copy_directory_contents(docs_dir))

        # Try skills/references/ or skills/docs/
        if 'skills_subdir' in structure:
            skills_refs = structure['skills_subdir'] / "references"
            if skills_refs.exists():
                docs.update(self._copy_directory_contents(skills_refs))
            skills_docs = structure['skills_subdir'] / "docs"
            if skills_docs.exists():
                docs.update(self._copy_directory_contents(skills_docs))

        return docs


    def _transform_script(self, content: str) -> str:
        """
        Transform a Python script for standalone use.

        Modifies scripts to accept file path as argument in addition
        to reading from stdin (Claude Code hook mode).

        Args:
            content: Original script content

        Returns:
            Transformed script content
        """
        # Replace ${CLAUDE_PLUGIN_ROOT} with relative path marker
        content = content.replace('${CLAUDE_PLUGIN_ROOT}', '.')

        return content

    def _copy_directory_contents(self, dir_path: Path) -> Dict[str, str]:
        """
        Copy all files from a directory, preserving structure.

        Args:
            dir_path: Directory to copy from

        Returns:
            Dict mapping relative path to content
        """
        files = {}

        if not dir_path.exists():
            return files

        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                try:
                    rel_path = file_path.relative_to(dir_path)
                    # Try to read as text
                    files[str(rel_path)] = file_path.read_text(encoding='utf-8')
                except (UnicodeDecodeError, PermissionError, OSError):
                    # Skip binary files, permission errors, or other I/O issues
                    continue

        return files

    def _generate_scripts_readme(self, source_dir: Path, structure: Dict[str, Path]) -> str:
        """
        Generate README for scripts directory explaining manual usage.

        Args:
            source_dir: Skill source directory
            structure: Detected skill structure

        Returns:
            README content
        """
        skill_name = source_dir.name

        # Find scripts directory
        scripts_dir = None
        if 'hooks_dir' in structure:
            scripts_dir = structure['hooks_dir'] / "scripts"
        elif 'scripts_dir' in structure:
            scripts_dir = structure['scripts_dir']

        readme = f"""# {skill_name} Scripts

These scripts provide automation and analysis for {skill_name}. In Claude Code,
they may run automatically via hooks. For other CLIs, run them manually.

## Usage

```bash
# Run a script
python scripts/<script_name>.py [arguments]

# Example
python scripts/<script_name>.py [options]
```

## Available Scripts

"""

        if scripts_dir and scripts_dir.exists():
            for script in sorted(scripts_dir.glob("*.py")):
                readme += f"- `{script.name}` - "
                # Try to extract description from docstring
                try:
                    content = script.read_text(encoding='utf-8')
                    docstring_match = re.search(r'"""([^"]+)"""', content)
                    if docstring_match:
                        desc = docstring_match.group(1).strip().split('\n')[0]
                        readme += desc
                    else:
                        readme += "Automation script"
                except Exception:
                    readme += "Automation script"
                readme += "\n"
        else:
            readme += "(No scripts found)\n"

        readme += """
## Requirements

- Python 3.8+
- Dependencies vary by script (check imports)

## Note

These scripts were originally designed for Claude Code.
They accept command-line arguments for manual use.
"""

        return readme

    def _common_skill_md_transforms(self, content: str) -> str:
        """
        Apply common SKILL.md transformations for all CLIs.

        Args:
            content: Original SKILL.md content

        Returns:
            Transformed content
        """
        # Remove ${CLAUDE_PLUGIN_ROOT} references
        content = content.replace('${CLAUDE_PLUGIN_ROOT}', '.')

        # Update Skill() invocation syntax to generic form
        # Skill(skill="{skill-name}", args="...") → @{skill-name} ...
        content = re.sub(
            r'Skill\(skill="([^"]+)"(?:,\s*args="([^"]*)")?\)',
            r'@\1 \2',
            content
        )

        return content

    def write_output(self, output: SkillOutput, target_dir: Path) -> None:
        """
        Write transformed skill output to target directory.

        Args:
            output: SkillOutput with transformed files
            target_dir: Directory to write to
        """
        # Create target directory
        target_dir.mkdir(parents=True, exist_ok=True)

        # Write SKILL.md
        try:
            (target_dir / "SKILL.md").write_text(output.skill_md, encoding='utf-8')
        except (PermissionError, OSError) as e:
            raise OSError(f"Failed to write SKILL.md to {target_dir}: {e}") from e

        # Write scripts
        if output.scripts:
            scripts_dir = target_dir / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            for rel_path, content in output.scripts.items():
                try:
                    file_path = scripts_dir / rel_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding='utf-8')
                except (PermissionError, OSError) as e:
                    raise OSError(f"Failed to write script {rel_path}: {e}") from e

        # Write templates/assets
        if output.templates:
            templates_dir = target_dir / self.templates_dir_name
            templates_dir.mkdir(exist_ok=True)
            for rel_path, content in output.templates.items():
                try:
                    file_path = templates_dir / rel_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding='utf-8')
                except (PermissionError, OSError) as e:
                    raise OSError(f"Failed to write template {rel_path}: {e}") from e

        # Write docs/references
        if output.docs:
            docs_dir = target_dir / self.docs_dir_name
            docs_dir.mkdir(exist_ok=True)
            for rel_path, content in output.docs.items():
                try:
                    file_path = docs_dir / rel_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding='utf-8')
                except (PermissionError, OSError) as e:
                    raise OSError(f"Failed to write doc {rel_path}: {e}") from e

        # Write examples
        if output.examples:
            examples_dir = target_dir / "examples"
            examples_dir.mkdir(exist_ok=True)
            for rel_path, content in output.examples.items():
                try:
                    file_path = examples_dir / rel_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding='utf-8')
                except (PermissionError, OSError) as e:
                    raise OSError(f"Failed to write example {rel_path}: {e}") from e

        # Write CLI-specific files
        for rel_path, content in output.cli_specific.items():
            try:
                file_path = target_dir / rel_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding='utf-8')
            except (PermissionError, OSError) as e:
                raise OSError(f"Failed to write CLI-specific file {rel_path}: {e}") from e
