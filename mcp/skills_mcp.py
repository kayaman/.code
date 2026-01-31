#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.0"]
# ///
"""
Skills MCP Server for Cursor.
Discovers and invokes skills from a configurable skills directory.

Usage: uv run mcp/skills_mcp.py [--skills-dir .claude/skills]
"""

import argparse
from pathlib import Path

from mcp import FastMCP

app = FastMCP("cursor-skills")

SKILLS_DIR: Path = Path(".claude/skills")


def get_skills() -> dict[str, dict]:
    """Scan skills directory and return metadata for each skill."""
    skills = {}
    if not SKILLS_DIR.exists():
        return skills

    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        skill_dir = skill_md.parent
        skill_name = str(skill_dir.relative_to(SKILLS_DIR))

        description = ""
        content = skill_md.read_text()
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].split("\n"):
                    if line.strip().startswith("description:"):
                        description = line.split("description:", 1)[1].strip().strip("\"'")
                        break

        if not description:
            for line in content.split("\n"):
                if line.startswith("# "):
                    description = line[2:].strip()
                    break

        skills[skill_name] = {
            "skill_md": str(skill_md),
            "description": description,
        }

    return skills


@app.tool()
def list_skills() -> str:
    """List all available skills in the local skills directory."""
    skills = get_skills()
    if not skills:
        return "No skills found. Check that the skills directory exists and contains SKILL.md files."

    lines = ["**Available skills:**\n"]
    for name, info in skills.items():
        lines.append(f"- **{name}**: {info['description']}")
    return "\n".join(lines)


@app.tool()
def invoke_skill(skill_name: str) -> str:
    """
    Load and return the full instructions for a specific skill.

    Args:
        skill_name: Directory name of the skill (e.g. 'pdf-generator')
    """
    skills = get_skills()
    if skill_name not in skills:
        available = ", ".join(skills.keys()) if skills else "none"
        return f"Skill '{skill_name}' not found. Available: {available}"

    skill_md_path = Path(skills[skill_name]["skill_md"])
    content = skill_md_path.read_text()

    skill_dir = skill_md_path.parent
    extra_files = [
        str(f.relative_to(skill_dir))
        for f in sorted(skill_dir.rglob("*"))
        if f.is_file() and f.name != "SKILL.md"
    ]

    result = f"=== Skill: {skill_name} ===\n\n{content}"
    if extra_files:
        result += "\n\n=== Supporting files ===\n" + "\n".join(f"- {f}" for f in extra_files)

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skills MCP Server for Cursor")
    parser.add_argument(
        "--skills-dir",
        type=str,
        default=".claude/skills",
        help="Path to skills directory (default: .claude/skills)",
    )
    args = parser.parse_args()

    SKILLS_DIR = Path(args.skills_dir)
    app.run()
