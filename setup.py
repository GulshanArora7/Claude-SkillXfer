"""Setup script for claude-skillxfer."""

from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="claude-skillxfer",
    version="0.1.0",
    author="Claude SkillXfer Contributors",
    description="Convert Claude skills to Any Agentic Coding CLI Skills",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GulshanArora7/Claude-SkillXfer",
    packages=find_packages(exclude=['claude-skillxfer']),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "claude-skillxfer=claude_skillxfer.cli:main",
        ],
    },
)
