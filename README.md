# Claude SkillXfer

🔄 **Convert Claude Skills to Any Agentic Coding CLI Skills**

Claude SkillXfer is a universal converter that transforms Claude skills to work with different agentic coding CLIs, following the [Agent Skills open standard](https://agentskills.io).

## Features

- 🔍 **Auto-detects repository structure** - Works with any Claude skills repository
- 🌐 **Git URL support** - Clone and convert skills directly from GitHub/GitLab URLs
- 🎯 **Supports 6+ CLIs** - Cursor, Gemini, OpenCode, Codex, Droid, and more
- 🚀 **Easy to use** - Simple CLI interface
- 🔧 **Flexible** - Install to custom directories or use CLI defaults
- 📦 **Zero dependencies** - Pure Python, no external dependencies (except git for cloning)

## Installation

```bash
# Install from source
git clone https://github.com/GulshanArora7/Claude-SkillXfer.git
cd Claude-SkillXfer
pip install .

# Or install directly
pip install git+https://github.com/GulshanArora7/Claude-SkillXfer.git
```

## Quick Start

### From GitHub Repository

```bash
# List available skills from a GitHub repository
claude-skillxfer --repo https://github.com/user/claude-skills --list

# Install all skills for Cursor (automatically clones the repo)
claude-skillxfer --repo https://github.com/user/claude-skills --cli cursor --all

# Install specific skills for Gemini
claude-skillxfer --repo https://github.com/user/claude-skills --cli gemini --skills skill-name-1 skill-name-2

# Auto-detect installed CLIs and install all skills
claude-skillxfer --repo https://github.com/user/claude-skills --detect --all

# Install to a custom directory
claude-skillxfer --repo https://github.com/user/claude-skills --cli cursor --target /path/to/project --all

# Keep cloned repository (default: it is removed after installation)
claude-skillxfer --repo https://github.com/user/claude-skills --cli cursor --all --keep-clone
```

### Skills in a subdirectory

When skills live in a subdirectory of the repo (e.g. `parent-directory/skills`), use `--sub-dir`:

```bash
claude-skillxfer --repo https://git-repo/username/reponame --sub-dir parent-directory/skills --cli cursor --all
claude-skillxfer --repo /path/to/repo --sub-dir parent-directory/skills --list
```

### From Local Repository

```bash
# List available skills in a local repository
claude-skillxfer --repo /path/to/desire/claude-skills-repo --list

# Install all skills for Cursor
claude-skillxfer --repo /path/to/desire/claude-skills-repo --cli cursor --all
```

## Supported CLIs

| CLI             | Default Path        | Description                |
| --------------- | ------------------- | -------------------------- |
| **Cursor**      | `.cursor/rules/`    | Cursor IDE with MDC format |
| **Gemini**      | `~/.gemini/skills/` | Google Gemini CLI          |
| **OpenCode**    | `.opencode/skill/`  | OpenCode CLI               |
| **Codex**       | `.codex/skills/`    | OpenAI Codex CLI           |
| **Droid**       | `.factory/skills/`  | Factory.ai Droid CLI       |
| **Antigravity** | `.agent/skills/`    | Google Antigravity         |

## Usage Examples

### Install to a Desired Project Directory

```bash
# Install skills to your project's .cursor/rules/ directory
claude-skillxfer --repo /path/to/desire/claude-skills-repo --cli cursor --target /path/to/my-project --all
```

This creates: `/path/to/my-project/.cursor/rules/{skill-name}/`

### Install to Default CLI Location

```bash
# Install to Cursor's default location (current directory)
claude-skillxfer --repo /path/to/desire/claude-skills-repo --cli cursor --all
```

This creates: `./.cursor/rules/{skill-name}/`

### Auto-detect Installed CLIs

```bash
# Automatically detect installed CLIs and install all skills
claude-skillxfer --repo /path/to/desire/claude-skills-repo --detect --all
```

## Repository Structure Support

Claude SkillXfer automatically detects and supports multiple repository layouts:

### Direct Structure

```
skill-name/
├── SKILL.md
├── scripts/
├── references/
└── assets/
```

### Nested Structure

```
skill-name/
├── skills/
│   ├── SKILL.md
│   ├── scripts/
│   └── references/
```

### Hooks Structure

```
skill-name/
├── SKILL.md
├── hooks/
│   └── scripts/
└── templates/
```

## How It Works

1. **Accepts repository** - Works with Git URLs (GitHub, GitLab, etc.) or local paths
2. **Clones if needed** - Automatically clones git repositories to a temporary directory
3. **Detects repository structure** - Automatically finds skills regardless of layout
4. **Transforms SKILL.md** - Removes Claude Code-specific syntax for target CLI
5. **Copies supporting files** - Scripts, templates, references, and assets
6. **Applies CLI naming** - Installs skills with their original names
7. **Creates CLI structure** - Installs to CLI-specific directories
8. **Cleanup** - Cloned repositories are removed after installation by default (use `--keep-clone` to keep them)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Adding Support for New CLIs

To add support for a new CLI:

1. Create a new adapter in `claude_skillxfer/cli_adapters/`
2. Inherit from `CLIAdapter` and implement required methods
3. Register it in `claude_skillxfer/cli_adapters/__init__.py`
4. Add detection logic in `cli.py`'s `detect_installed_clis()` function

See existing adapters for examples.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Built following the [Agent Skills open standard](https://agentskills.io).

## Support

- 📖 [Documentation](https://github.com/GulshanArora7/Claude-SkillXfer#readme)
- 🐛 [Issue Tracker](https://github.com/GulshanArora7/Claude-SkillXfer/issues)
- 💬 [Discussions](https://github.com/GulshanArora7/Claude-SkillXfer/discussions)

---

Made with ❤️ for the agentic coding community
