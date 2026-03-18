"""Unified diff parser."""

import re
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class DiffLine:
    line_num: Optional[int]
    line_type: str  # 'ctx', 'add', 'del', 'empty', 'hunk_header'
    content: str


@dataclass
class DiffRow:
    old: DiffLine
    new: DiffLine


@dataclass
class FileDiff:
    old_path: str
    new_path: str
    display_path: str
    is_new: bool
    is_deleted: bool
    is_binary: bool
    rows: List[DiffRow]


def parse_diff(diff_text: str) -> List[FileDiff]:
    """Parse unified diff text into a list of FileDiff objects."""
    files: List[FileDiff] = []
    current_file: Optional[FileDiff] = None
    lines = diff_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # File header
        if line.startswith("diff --git "):
            m = re.match(r"^diff --git a/(.*) b/(.*)$", line)
            if m:
                if current_file:
                    files.append(current_file)
                current_file = FileDiff(
                    old_path=m.group(1),
                    new_path=m.group(2),
                    display_path=m.group(2),
                    is_new=False,
                    is_deleted=False,
                    is_binary=False,
                    rows=[],
                )
            i += 1
            continue

        if line.startswith("new file mode"):
            if current_file:
                current_file.is_new = True
            i += 1
            continue

        if line.startswith("deleted file mode"):
            if current_file:
                current_file.is_deleted = True
            i += 1
            continue

        if line.startswith("Binary files"):
            if current_file:
                current_file.is_binary = True
            i += 1
            continue

        if line.startswith(("index ", "--- ", "+++ ", "old mode", "new mode",
                            "similarity index", "rename from", "rename to",
                            "copy from", "copy to")):
            i += 1
            continue

        # Hunk header
        hunk_m = re.match(
            r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)$", line
        )
        if hunk_m and current_file:
            old_num = int(hunk_m.group(1))
            new_num = int(hunk_m.group(2))
            ctx = hunk_m.group(3).strip()

            current_file.rows.append(DiffRow(
                old=DiffLine(None, "hunk_header", ctx or "..."),
                new=DiffLine(None, "hunk_header", ctx or "..."),
            ))

            i += 1
            while i < len(lines):
                hl = lines[i]

                if hl.startswith("diff --git ") or hl.startswith("@@ "):
                    break

                if hl.startswith("\\"):
                    i += 1
                    continue

                if hl.startswith(" "):
                    current_file.rows.append(DiffRow(
                        old=DiffLine(old_num, "ctx", hl[1:]),
                        new=DiffLine(new_num, "ctx", hl[1:]),
                    ))
                    old_num += 1
                    new_num += 1
                    i += 1
                elif hl.startswith("-") or hl.startswith("+"):
                    removes: List[DiffLine] = []
                    adds: List[DiffLine] = []
                    while i < len(lines) and lines[i].startswith("-"):
                        removes.append(
                            DiffLine(old_num, "del", lines[i][1:])
                        )
                        old_num += 1
                        i += 1
                    while i < len(lines) and lines[i].startswith("\\"):
                        i += 1
                    while i < len(lines) and lines[i].startswith("+"):
                        adds.append(
                            DiffLine(new_num, "add", lines[i][1:])
                        )
                        new_num += 1
                        i += 1
                    while i < len(lines) and lines[i].startswith("\\"):
                        i += 1

                    max_len = max(len(removes), len(adds))
                    for j in range(max_len):
                        old_line = (
                            removes[j] if j < len(removes)
                            else DiffLine(None, "empty", "")
                        )
                        new_line = (
                            adds[j] if j < len(adds)
                            else DiffLine(None, "empty", "")
                        )
                        current_file.rows.append(
                            DiffRow(old=old_line, new=new_line)
                        )
                elif hl == "":
                    if (i + 1 < len(lines) and
                            (lines[i + 1].startswith(" ") or
                             lines[i + 1].startswith("+") or
                             lines[i + 1].startswith("-") or
                             lines[i + 1].startswith("\\"))):
                        current_file.rows.append(DiffRow(
                            old=DiffLine(old_num, "ctx", ""),
                            new=DiffLine(new_num, "ctx", ""),
                        ))
                        old_num += 1
                        new_num += 1
                        i += 1
                    else:
                        break
                else:
                    i += 1
            continue

        i += 1

    if current_file:
        files.append(current_file)

    return files
