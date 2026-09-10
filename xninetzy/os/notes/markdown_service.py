from __future__ import annotations

import re
from typing import Any


class MarkdownService:
    def parse_frontmatter(self, content: str) -> dict[str, Any]:
        if not content.startswith("---\n"):
            return {}
        end = content.find("\n---\n", 4)
        if end == -1:
            return {}

        data: dict[str, Any] = {}
        for line in content[4:end].splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            raw = value.strip()
            if raw.startswith("[") and raw.endswith("]"):
                items = [item.strip().strip("\"'") for item in raw[1:-1].split(",") if item.strip()]
                data[key.strip()] = items
            else:
                data[key.strip()] = raw.strip("\"'")
        return data

    def upsert_frontmatter(self, content: str, data: dict[str, Any]) -> str:
        existing = self.parse_frontmatter(content)
        merged = {**existing, **data}
        frontmatter = ["---"]
        for key, value in merged.items():
            if isinstance(value, list):
                rendered = ", ".join(str(item) for item in value)
                frontmatter.append(f"{key}: [{rendered}]")
            else:
                frontmatter.append(f"{key}: {value}")
        frontmatter.append("---")

        body = content
        if content.startswith("---\n"):
            end = content.find("\n---\n", 4)
            if end != -1:
                body = content[end + 5 :].lstrip("\n")

        return "\n".join(frontmatter) + "\n\n" + body

    def extract_headings(self, content: str) -> list[dict[str, Any]]:
        headings: list[dict[str, Any]] = []
        for line_no, line in enumerate(content.splitlines(), start=1):
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                headings.append({"level": len(match.group(1)), "title": match.group(2).strip(), "line": line_no})
        return headings

    def update_heading_section(self, content: str, heading: str, new_content: str) -> str:
        lines = content.splitlines()
        heading_index = self._find_heading_index(lines, heading)
        if heading_index is None:
            suffix = "" if content.endswith("\n") else "\n"
            return content + suffix + f"\n## {heading}\n{new_content.strip()}\n"

        heading_level = len(lines[heading_index].split(" ", 1)[0])
        end_index = len(lines)
        for index in range(heading_index + 1, len(lines)):
            match = re.match(r"^(#{1,6})\s+", lines[index])
            if match and len(match.group(1)) <= heading_level:
                end_index = index
                break

        replacement = [lines[heading_index], "", new_content.strip()]
        return "\n".join(lines[: heading_index + 1] + replacement[1:] + lines[end_index:]).rstrip() + "\n"

    def append_todo(self, content: str, todo: str) -> str:
        return self.update_heading_section(content, "Task", self._section_content(content, "Task") + f"\n- [ ] {todo.strip()}")

    def add_tags(self, content: str, tags: list[str]) -> str:
        existing = self.parse_frontmatter(content)
        current = existing.get("tags", [])
        if not isinstance(current, list):
            current = [str(current)]
        merged = sorted({tag.strip().lstrip("#") for tag in [*current, *tags] if tag.strip()})
        return self.upsert_frontmatter(content, {"tags": merged})

    def add_backlinks(self, content: str, links: list[str]) -> str:
        rendered = "\n".join(f"- {self.wikilink(link)}" for link in links if link.strip())
        return self.update_heading_section(content, "Related", self._section_content(content, "Related") + "\n" + rendered)

    def wikilink(self, target: str, display: str | None = None, heading: str | None = None) -> str:
        clean_target = target.strip().strip("[]")
        if heading:
            clean_target = f"{clean_target}#{heading.strip().lstrip('#')}"
        if display:
            return f"[[{clean_target}|{display.strip()}]]"
        return f"[[{clean_target}]]"

    def embed(self, target: str, width: int | None = None) -> str:
        clean_target = target.strip().strip("[]")
        if width:
            clean_target = f"{clean_target}|{width}"
        return f"![[{clean_target}]]"

    def callout(self, kind: str, body: str, title: str | None = None, folded: str | None = None) -> str:
        suffix = folded if folded in {"-", "+"} else ""
        header = f"> [!{kind.strip().lower()}]{suffix}"
        if title:
            header += f" {title.strip()}"
        quoted_body = "\n".join(f"> {line}" if line else ">" for line in body.strip().splitlines())
        return f"{header}\n{quoted_body}"

    def _find_heading_index(self, lines: list[str], heading: str) -> int | None:
        target = heading.strip().casefold()
        for index, line in enumerate(lines):
            match = re.match(r"^#{1,6}\s+(.+)$", line)
            if match and match.group(1).strip().casefold() == target:
                return index
        return None

    def _section_content(self, content: str, heading: str) -> str:
        lines = content.splitlines()
        heading_index = self._find_heading_index(lines, heading)
        if heading_index is None:
            return ""

        heading_level = len(lines[heading_index].split(" ", 1)[0])
        section: list[str] = []
        for line in lines[heading_index + 1 :]:
            match = re.match(r"^(#{1,6})\s+", line)
            if match and len(match.group(1)) <= heading_level:
                break
            section.append(line)
        return "\n".join(section).strip()
