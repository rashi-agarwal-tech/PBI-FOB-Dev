"""
Script to fix commit links in CHANGELOG.md by removing "https://github.com//" and
appending "?refName=refs%2Fheads%2Fdevelopment" to commit reference links. This 
due to the fact that, cz-github-jira-conventional, does not support Azure DevOps
and I could not find a plugin for commitizen that does.....
"""

import re
import os
from pathlib import Path


def fix_changelog():
    """Fix the commit links in CHANGELOG.md."""
    print("Fixing CHANGELOG.md...")

    # Get the path to the CHANGELOG.md file (assuming it's in the project root)
    # Run this with just fix-chnagelog, runs in pipeline.
    project_root = Path(__file__).parent.parent
    changelog_file = project_root / "CHANGELOG.md"
    temp_file = project_root / "CHANGELOG.tmp"

    with open(changelog_file, "r", encoding="utf-8") as input_file:
        with open(temp_file, "w", encoding="utf-8") as output_file:
            for line in input_file:
                modified_line = re.sub(
                    r"https://github\.com//(\S+/commit/[a-f0-9]+)",
                    r"\1?refName=refs%2Fheads%2Fdevelopment",
                    line,
                )
                output_file.write(modified_line)

    os.replace(temp_file, changelog_file)

    print("CHANGELOG.md has been updated successfully!")


if __name__ == "__main__":
    fix_changelog()
