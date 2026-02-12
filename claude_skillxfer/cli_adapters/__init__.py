"""
CLI Adapters for Claude Skills Multi-CLI Installer.

This package provides adapters for transforming Claude skills to different
agentic coding CLI formats following the Agent Skills open standard.

Supported CLIs:
- OpenCode: .opencode/skill/{name}/
- Codex CLI: .codex/skills/{name}/
- Gemini CLI: ~/.gemini/skills/{name}/
- Droid CLI: .factory/skills/{name}/
- Cursor: .cursor/rules/{name}.mdc (MDC format)
- Antigravity: .agent/skills/{name}/ (Google Antigravity)
"""

from .base import CLIAdapter, SkillOutput
from .opencode import OpenCodeAdapter
from .codex import CodexAdapter
from .gemini import GeminiAdapter
from .droid import DroidAdapter
from .cursor import CursorAdapter
from .antigravity import AntigravityAdapter

# Registry of available adapters
ADAPTERS = {
    'opencode': OpenCodeAdapter,
    'codex': CodexAdapter,
    'gemini': GeminiAdapter,
    'droid': DroidAdapter,
    'cursor': CursorAdapter,
    'antigravity': AntigravityAdapter,
}

__all__ = [
    'CLIAdapter',
    'SkillOutput',
    'OpenCodeAdapter',
    'CodexAdapter',
    'GeminiAdapter',
    'DroidAdapter',
    'CursorAdapter',
    'AntigravityAdapter',
    'ADAPTERS',
]
