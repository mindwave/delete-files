#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.reactive import reactive
from textual.widgets import Button, DataTable, Footer, Header, Label, Static

# ---------- Helpers ----------

@dataclass
class FileRow:
    checked: bool
    name: str
    modified: str
    size: str
    path: Path


def fmt_size(n: int) -> str:
    # Human-ish readable sizes
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def fmt_mtime(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def scan_files(directory: Path) -> Iterable[FileRow]:
    with os.scandir(directory) as it:
        for entry in it:
            if entry.is_file(follow_symlinks=False):
                stat = entry.stat(follow_symlinks=False)
                yield FileRow(
                    checked=False,
                    name=entry.name,
                    modified=fmt_mtime(stat.st_mtime),
                    size=fmt_size(stat.st_size),
                    path=Path(entry.path),
                )


# ---------- Confirmation Modal ----------

class ConfirmDelete(ModalScreen[bool]):
    """Simple yes/no confirmation modal."""

    def __init__(self, count: int):
        super().__init__()
        self.count = count

    def compose(self) -> ComposeResult:
        msg = "file" if self.count == 1 else "files"
        yield Static(f"Delete {self.count} {msg}? This cannot be undone.", classes="confirm-text")
        with Horizontal(classes="confirm-buttons"):
            yield Button("Cancel", id="cancel", variant="default")
            yield Button("Delete", id="delete", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "delete")


# ---------- Main App ----------

class FileDeleteApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    .titlebar {
        padding: 1 2;
        border-bottom: tall $surface;
    }
    #table {
        height: 1fr;
    }
    .controls {
        padding: 1 2;
        border-top: tall $surface;
        dock: bottom;
    }
    .spacer {
        width: 1fr;
    }
    .confirm-text {
        padding: 2 4;
    }
    .confirm-buttons {
        padding: 0 4 2 4;
        width: 100%;
        align-horizontal: right;
        content-align: right middle;
    }
    """

    BINDINGS = [
        Binding("space", "toggle_check", "Toggle check"),
        Binding("d", "delete_checked", "Delete checked"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    directory: reactive[Path] = reactive(Path.cwd())

    def __init__(self, directory: Path):
        super().__init__()
        self.directory = directory
        self.table: DataTable | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(classes="titlebar"):
            yield Label(f"Directory: {self.directory}")
            yield Label("Tip: Space=toggle, D=delete, R=refresh, Q=quit", id="tip")
        self.table = DataTable(id="table", cursor_type="row")
        yield self.table
        with Horizontal(classes="controls"):
            yield Button("Refresh", id="refresh", variant="default")
            yield Button("Delete Checked", id="delete", variant="error")
            yield Static("", classes="spacer")
        yield Footer()

    # ---------- Table setup / refresh ----------

    def on_mount(self) -> None:
        self._setup_table()
        self._load_rows()

    def _setup_table(self) -> None:
        t = self.table
        assert t is not None
        t.clear(columns=True)
        # We'll store the absolute path in a hidden 5th column
        t.add_columns("✓", "Name", "Modified", "Size", "Path")
        # t.set_column_width(0, 3)
        # t.set_column_width(1, 40)
        # t.set_column_width(2, 18)
        # t.set_column_width(3, 10)
        # t.set_column_visibility(4, False)

    def _load_rows(self) -> None:
        assert self.table is not None
        self.table.clear()
        rows = list(scan_files(self.directory))
        for row in rows:
            self.table.add_row(
                "☐",
                row.name,
                row.modified,
                row.size,
                str(row.path)
            )
        self.notify(f"Loaded {len(rows)} file(s).", timeout=3)

    # ---------- Interactions ----------

    def action_refresh(self) -> None:
        self._load_rows()

    def action_toggle_check(self) -> None:
        t = self.table
        assert t is not None
        if t.cursor_row is None:
            return
        current = t.get_cell_at(t.cursor_row, 0)
        new_val = "☐" if current == "☑" else "☑"
        t.update_cell_at(t.cursor_row, 0, new_val)

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        # Toggle if they click the checkbox column
        if event.coordinate.column == 0:
            current = self.table.get_cell_at(event.coordinate.row, 0)
            new_val = "☐" if current == "☑" else "☑"
            self.table.update_cell_at(event.coordinate.row, 0, new_val)

    def _checked_paths(self) -> list[Path]:
        assert self.table is not None
        checked: list[Path] = []
        for row_key in self.table.rows:
            row = self.table.get_row(row_key)
            if row[0] == "☑":
                checked.append(Path(row[4]))
        return checked

    async def action_delete_checked(self) -> None:
        paths = self._checked_paths()
        if not paths:
            self.notify("No files checked.", severity="warning", timeout=3)
            return
        proceed = await self.push_screen(ConfirmDelete(len(paths)))
        if proceed:
            self._delete_files(paths)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh":
            self.action_refresh()
        elif event.button.id == "delete":
            self.call_from_thread(lambda: self.post_message(Message("delete_request")))
            # Use same logic as keybinding
            self.run_worker(self.action_delete_checked(), exclusive=True)

    # ---------- Deletion ----------

    def _delete_files(self, paths: list[Path]) -> None:
        assert self.table is not None
        deleted = 0
        errors: list[tuple[Path, str]] = []

        # Build a map from path -> row_key to remove efficiently
        path_to_row = {}
        for row_key in self.table.rows:
            row = self.table.get_row(row_key)
            path_to_row[Path(row[4])] = row_key

        for p in paths:
            try:
                # Safety: only delete files in the chosen directory
                if not p.is_file():
                    errors.append((p, "Not a file"))
                    continue
                if p.parent.resolve() != self.directory.resolve():
                    errors.append((p, "Outside selected directory"))
                    continue
                p.unlink()
                deleted += 1
                row_key = path_to_row.get(p)
                if row_key is not None:
                    self.table.remove_row(row_key)
            except Exception as e:
                errors.append((p, str(e)))

        msg = f"Deleted {deleted} file(s)."
        if errors:
            msg += f" {len(errors)} error(s)."
            # Show a brief summary in the UI
            self.notify(
                msg + " Check terminal for details.",
                severity="error" if deleted == 0 else "warning",
                timeout=5,
            )
            for p, err in errors:
                print(f"[ERROR] {p}: {err}", file=sys.stderr)
        else:
            self.notify(msg, timeout=4)


def main():
    parser = argparse.ArgumentParser(description="Textual file deletion checklist")
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to list (default: current directory)",
    )
    args = parser.parse_args()
    directory = Path(args.directory).expanduser().resolve()
    if not directory.exists() or not directory.is_dir():
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        sys.exit(2)
    app = FileDeleteApp(directory)
    app.run()


if __name__ == "__main__":
    main()