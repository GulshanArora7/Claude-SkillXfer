# Quick Start Guide

Get started with Claude SkillXfer in 5 minutes!

## Installation

```bash
# Install from source
git clone https://github.com/GulshanArora7/Claude-SkillXfer.git
cd Claude-SkillXfer
pip install .
```

## Basic Usage

### 1. List Available Skills

```bash
claude-skillxfer --repo /path/to/desire/claude-skills-repo --list
```

### 2. Install Skills for a CLI

```bash
# From GitHub - Install all skills for Cursor
claude-skillxfer --repo /path/to/desire/claude-skills-repo --cli cursor --all

# From local - Install specific skills
claude-skillxfer --repo /path/to/desire/claude-skills-repo --cli cursor --skills skill-name-1 skill-name-2
```

### 3. Install to Your Project

```bash
# Install to your project directory
claude-skillxfer --repo /path/to/desire/claude-skills-repo \
  --cli cursor \
  --target /path/to/your/project \
  --all
```

This creates: `/path/to/your/project/.cursor/rules/{skill-name}/`

### 4. Auto-detect and Install

```bash
# Automatically detect installed CLIs and install all skills
claude-skillxfer --repo /path/to/desire/claude-skills-repo --detect --all
```

## Common Workflows

### Convert Skills for Cursor

```bash
claude-skillxfer --repo /path/to/desire/claude-skills-repo --cli cursor --all --target .
```

### Convert Skills for Gemini

```bash
claude-skillxfer --repo /path/to/desire/claude-skills-repo --cli gemini --all
```

### Convert Specific Skills

```bash
claude-skillxfer --repo /path/to/desire/claude-skills-repo \
  --cli cursor \
  --skills skill-name-1 skill-name-2 \
  --target ./my-project
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [CONTRIBUTING.md](CONTRIBUTING.md) to add support for new CLIs
- Report issues or suggest features on GitHub
