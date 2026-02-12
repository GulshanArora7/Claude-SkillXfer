#!/usr/bin/env python3
"""
Claude SkillXfer CLI

Convert Claude skills to different agentic coding CLIs.
"""

import argparse
import re
import shutil
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from .cli_adapters import ADAPTERS, CLIAdapter


# ANSI colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str) -> None:
    """Print a styled header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
    print("=" * len(text))


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.ENDC} {text}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.ENDC} {text}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.ENDC} {text}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ{Colors.ENDC} {text}")


def get_available_skills(repo_root: Path) -> List[str]:
    """
    Get list of available skills in the repository.

    Supports multiple repository structures:
    - Direct: skill-name/SKILL.md
    - Nested: skill-name/skills/SKILL.md

    Returns:
        List of skill directory names
    """
    skills = []
    for item in repo_root.iterdir():
        if item.is_dir() and not item.name.startswith(".") and item.name not in ["tools", "claude_skillxfer"]:
            # Check for SKILL.md at root or in skills/ subdirectory
            if (item / "SKILL.md").exists() or (item / "skills" / "SKILL.md").exists():
                skills.append(item.name)
    return sorted(skills)


def detect_installed_clis() -> List[str]:
    """
    Auto-detect which CLIs are installed on the system.

    Returns:
        List of detected CLI names
    """
    detected = []

    # Check for OpenCode
    if shutil.which("opencode") or Path.home().joinpath(".opencode").exists():
        detected.append("opencode")

    # Check for Codex CLI
    if shutil.which("codex"):
        detected.append("codex")

    # Check for Gemini CLI
    if shutil.which("gemini") or Path.home().joinpath(".gemini").exists():
        detected.append("gemini")

    # Check for Droid CLI (Factory.ai)
    if shutil.which("droid") or Path.home().joinpath(".factory").exists():
        detected.append("droid")

    # Check for Cursor (IDE with CLI)
    if shutil.which("cursor") or Path.home().joinpath(".cursor").exists():
        detected.append("cursor")

    # Check for Antigravity (.agent or ~/.gemini/antigravity)
    if (Path.cwd() / ".agent").exists() or Path.home().joinpath(".gemini", "antigravity").exists():
        detected.append("antigravity")

    return detected


def install_skill(
    adapter: CLIAdapter,
    skill_name: str,
    repo_root: Path,
    target_base: Optional[Path] = None
) -> bool:
    """
    Install a single skill using the specified adapter.

    Args:
        adapter: CLI adapter to use
        skill_name: Name of skill to install
        repo_root: Repository root directory
        target_base: Base directory for installation (uses adapter default if None)

    Returns:
        True if successful, False otherwise
    """
    source_dir = repo_root / skill_name

    if not source_dir.exists():
        print_error(f"Skill not found: {skill_name}")
        return False

    # Check for SKILL.md at root or in skills/ subdirectory
    skill_md_path = source_dir / "SKILL.md"
    if not skill_md_path.exists():
        skill_md_path = source_dir / "skills" / "SKILL.md"
        if not skill_md_path.exists():
            print_error(f"Invalid skill (no SKILL.md found): {skill_name}")
            return False

    try:
        # Transform skill for target CLI
        output = adapter.transform_skill(source_dir)

        # Determine target directory with CLI-specific naming
        install_name = adapter.get_skill_install_name(skill_name)
        
        if target_base:
            # If custom target is provided, create CLI structure under target
            # e.g., /target-path/.cursor/rules/{skill-name}/
            target_dir = target_base / adapter.relative_install_path / install_name
        else:
            # Use default CLI path with naming convention
            target_dir = adapter.default_install_path / install_name

        # Write output
        adapter.write_output(output, target_dir)

        print_success(f"Installed {skill_name} as {install_name} to {target_dir}")
        return True

    except Exception as e:
        print_error(f"Failed to install {skill_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def install_skills(
    cli: str,
    skills: List[str],
    repo_root: Path,
    target: Optional[Path] = None,
    force: bool = False
) -> int:
    """
    Install multiple skills for a CLI.

    Args:
        cli: Target CLI name
        skills: List of skills to install
        repo_root: Repository root directory
        target: Custom target directory (optional)
        force: Overwrite existing installations

    Returns:
        Number of successfully installed skills
    """
    if cli not in ADAPTERS:
        print_error(f"Unknown CLI: {cli}")
        print_info(f"Supported CLIs: {', '.join(ADAPTERS.keys())}")
        return 0

    adapter_class = ADAPTERS[cli]
    adapter = adapter_class(repo_root)

    # If target is specified, use it directly; otherwise use CLI default
    target_base = Path(target) if target else None

    print_header(f"Installing skills for {cli.upper()}")
    if target_base:
        print_info(f"Target directory: {target_base}")
    else:
        print_info(f"Target: {adapter.default_install_path} (CLI default)")
    print()

    success_count = 0
    for skill in skills:
        # Use CLI-specific naming
        install_name = adapter.get_skill_install_name(skill)
        if target_base:
            # Create CLI structure under target directory
            # e.g., /target-path/.cursor/rules/{skill-name}/
            target_dir = target_base / adapter.relative_install_path / install_name
        else:
            # Use CLI default path
            target_dir = adapter.default_install_path / install_name

        if target_dir.exists() and not force:
            print_warning(f"Skipping {skill} (already exists as {install_name}, use --force to overwrite)")
            continue

        if target_dir.exists() and force:
            shutil.rmtree(target_dir)

        if install_skill(adapter, skill, repo_root, target_base):
            success_count += 1

    return success_count


def list_skills(repo_root: Path) -> None:
    """List all available skills with descriptions."""
    print_header("Available Skills")

    skills = get_available_skills(repo_root)

    if not skills:
        print_warning("No skills found in repository")
        return

    for skill in skills:
        skill_md = repo_root / skill / "SKILL.md"
        if not skill_md.exists():
            skill_md = repo_root / skill / "skills" / "SKILL.md"
        
        if skill_md.exists():
            content = skill_md.read_text(encoding='utf-8')
            # Extract description from YAML frontmatter
            desc_match = re.search(r'description:\s*[>|]?\s*\n?\s*(.+?)(?:\n\w|\n---)', content, re.DOTALL)
            if desc_match:
                desc = desc_match.group(1).strip().replace('\n', ' ')[:60]
                print(f"  {Colors.CYAN}{skill:25}{Colors.ENDC} {desc}...")
            else:
                print(f"  {Colors.CYAN}{skill:25}{Colors.ENDC}")
        else:
            print(f"  {Colors.CYAN}{skill:25}{Colors.ENDC} (no description)")


def list_clis(repo_root: Path) -> None:
    """List supported CLIs and their install paths."""
    print_header("Supported CLIs")

    for name, adapter_class in ADAPTERS.items():
        adapter = adapter_class(repo_root)
        print(f"  {Colors.CYAN}{name:15}{Colors.ENDC} → {adapter.default_install_path}")

    print()
    detected = detect_installed_clis()
    if detected:
        print_info(f"Detected on this system: {', '.join(detected)}")
    else:
        print_warning("No supported CLIs detected on this system")


def resolve_repository(repo_path: str, sub_dir: Optional[str] = None) -> tuple[Path, bool]:
    """
    Resolve repository path from URL or local path.

    If sub_dir is given, the skills root is that subdirectory inside the repo
    (e.g. parent-directory/skills). Use --sub-dir when skills are not at repo root.

    Returns:
        Tuple of (Path to repository/skills directory, is_cloned)
    """
    # Check if it's a URL
    parsed = urlparse(repo_path)
    is_url = parsed.scheme in ('http', 'https', 'git') or repo_path.startswith('git@')
    
    if is_url:
        # It's a git URL - clone it to a temporary directory
        print_info(f"Cloning repository: {repo_path}")
        temp_dir = tempfile.mkdtemp(prefix="claude-skillxfer-")
        
        try:
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', repo_path, temp_dir],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print_error(f"Failed to clone repository: {result.stderr}")
                raise ValueError(f"Git clone failed: {result.stderr}")
            
            print_success(f"Repository cloned to: {temp_dir}")
            repo_root = Path(temp_dir)
        except subprocess.TimeoutExpired:
            print_error("Repository clone timed out")
            raise
        except FileNotFoundError:
            print_error("Git is not installed. Please install git to clone repositories.")
            raise
    else:
        # It's a local path
        repo_root = Path(repo_path).resolve()
        if not repo_root.exists():
            print_error(f"Repository not found: {repo_root}")
            raise ValueError(f"Repository not found: {repo_root}")
        
        if not repo_root.is_dir():
            print_error(f"Repository path is not a directory: {repo_root}")
            raise ValueError(f"Repository path is not a directory: {repo_root}")

    if sub_dir:
        sub_path = sub_dir.strip("/")
        repo_root = repo_root / sub_path
        if not repo_root.is_dir():
            print_error(f"Subdirectory not found: {repo_root}")
            raise ValueError(f"Subdirectory not found: {repo_root}")
    return repo_root, is_url


def main():
    parser = argparse.ArgumentParser(
        description="Convert Claude skills to different agentic coding CLIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From GitHub repository
  claude-skillxfer --repo https://github.com/user/claude-skills --cli cursor --all
  claude-skillxfer --repo https://github.com/user/claude-skills --cli gemini --skills {skill-name}
  
  # Repo with skills in a subdirectory
  claude-skillxfer --repo https://git-repo/username/reponame --sub-dir parent-dir/skills --cli cursor --all
  claude-skillxfer --repo /path/to/repo --sub-dir parent-dir/skills --list

  # From local repository
  claude-skillxfer --repo /path/to/skills --cli cursor --all
  claude-skillxfer --repo /path/to/skills --detect --all

  # List skills
  claude-skillxfer --repo https://github.com/user/claude-skills --list
  claude-skillxfer --repo /path/to/skills --list-clis
        """
    )

    # Repository path or URL
    parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="Git repository URL (https://github.com/user/repo) or local path to Claude skills repository"
    )
    parser.add_argument(
        "--sub-dir",
        type=str,
        metavar="PATH",
        dest="sub_dir",
        help="Path to skills root inside the repo when not at root (e.g. parent-dir/skills)"
    )

    # CLI selection
    cli_group = parser.add_mutually_exclusive_group()
    cli_group.add_argument(
        "--cli",
        choices=list(ADAPTERS.keys()),
        help="Target CLI to install for"
    )
    cli_group.add_argument(
        "--detect",
        action="store_true",
        help="Auto-detect installed CLIs"
    )

    # Skill selection
    skill_group = parser.add_mutually_exclusive_group()
    skill_group.add_argument(
        "--skills",
        nargs="+",
        help="Specific skills to install"
    )
    skill_group.add_argument(
        "--all",
        action="store_true",
        help="Install all available skills"
    )

    # Options
    parser.add_argument(
        "--target",
        type=str,
        help="Custom target directory for installation"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing installations"
    )
    parser.add_argument(
        "--keep-clone",
        action="store_true",
        help="Keep cloned repository after installation (default: remove it when using --repo URL)"
    )

    # Info commands
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available skills"
    )
    parser.add_argument(
        "--list-clis",
        action="store_true",
        help="List supported CLIs"
    )

    args = parser.parse_args()

    # Resolve repository (clone if URL, or use local path)
    try:
        repo_root, is_cloned = resolve_repository(args.repo, sub_dir=args.sub_dir)
    except Exception as e:
        print_error(f"Failed to resolve repository: {e}")
        return 1
    
    cloned_repo_path = repo_root if is_cloned else None  # removed after install unless --keep-clone

    # Handle info commands
    if args.list:
        list_skills(repo_root)
        return 0

    if args.list_clis:
        list_clis(repo_root)
        return 0

    # Validate required arguments for installation
    if not args.cli and not args.detect:
        parser.error("Either --cli or --detect is required for installation")

    if not args.skills and not args.all:
        parser.error("Either --skills or --all is required")

    # Get skills to install
    if args.all:
        skills = get_available_skills(repo_root)
    else:
        skills = args.skills

    if not skills:
        print_error("No skills to install")
        return 1

    # Get target CLIs
    if args.detect:
        target_clis = detect_installed_clis()
        if not target_clis:
            print_error("No supported CLIs detected on this system")
            print_info("Install one of: OpenCode, Codex CLI, Gemini CLI, Cursor, Droid CLI, or Antigravity")
            return 1
        print_info(f"Detected CLIs: {', '.join(target_clis)}")
    else:
        target_clis = [args.cli]

    # Install for each CLI
    total_success = 0
    total_skills = len(skills) * len(target_clis)

    for cli in target_clis:
        success = install_skills(
            cli=cli,
            skills=skills,
            repo_root=repo_root,
            target=args.target,
            force=args.force
        )
        total_success += success

    # Summary
    print()
    print_header("Installation Summary")
    print(f"  Skills installed: {total_success}/{total_skills}")

    if total_success == total_skills:
        print_success("All skills installed successfully!")
    elif total_success > 0:
        print_warning("Some skills failed to install")
    else:
        print_error("No skills were installed")

    exit_code = 0 if total_success > 0 else 1

    # Cleanup: remove cloned repo by default; keep only if --keep-clone
    if cloned_repo_path:
        if args.keep_clone:
            print_info(f"Cloned repository kept at: {cloned_repo_path}")
        else:
            try:
                shutil.rmtree(cloned_repo_path)
                print_success("Cloned repository removed")
            except Exception as e:
                print_warning(f"Failed to remove cloned repository: {e}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
