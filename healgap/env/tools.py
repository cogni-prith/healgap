"""The four agent tools over the visible database, and conversion of a rollout conversation to an Episode.

AgentTune's rollout gives tools only the model's arguments and never ends an episode on a tool call
(docs/DECISIONS.md, M0 items 1 and 2). So the tools read a per-episode context that a pre-step hook sets from
the task id in the prompt, and submit locks the episode: later tool calls are refused and the first submit counts.
Rollouts run one at a time, so one shared context is safe.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path

from healgap.env.dataset import Dataset, Episode, ToolCall
from healgap.env.sqlexec import run_sql

TASK_ID_RE = re.compile(r"R-\d{4}")
OVER = "The report was already submitted. This episode is over. Do not call any more tools."
SAVED = "Report saved. The task is complete."
NOT_ALONE = "Error: submit was ignored because it was called in the same turn as other tools. Read the results above, then call submit on its own."
NUDGE = " If this query answers the question, call submit with the same SQL now."
TOOL_NAMES = ("list_tables", "describe_table", "run_query", "submit")


class SqlEnv:
    def __init__(self, ds: Dataset, max_rows: int, timeout_s: float) -> None:
        self.ds, self.max_rows, self.timeout_s = ds, max_rows, timeout_s
        self.db: Path | None = None
        self.submitted = False
        self.calls_this_turn = 0

    def begin(self, task_id: str) -> None:
        self.db = self.ds.visible_db(self.ds.tasks[task_id].family)
        self.submitted = False

    def pre_step_hook(self, step: int, conversation: list[dict], tools: object = None) -> None:
        """AgentTune calls this before every model turn, with step 0 at the start of every rollout."""
        self.calls_this_turn = 0
        normalise_history(conversation)
        if step == 0:
            self.begin(task_id_of(conversation))

    def refuse(self) -> str | None:
        """Reason this tool call is not executed, or None."""
        if self.db is None:
            return "Error: no active episode."
        if self.submitted:
            return OVER
        self.calls_this_turn += 1
        return None

    def query(self, sql: str, max_rows: int | None) -> str:
        no = self.refuse()
        if no:
            return no
        rows, err = run_sql(self.db, sql, max_rows=max_rows, timeout_s=self.timeout_s)
        return f"Error: {err}" if rows is None else json.dumps(rows)


def normalise_history(conversation: list[dict]) -> None:
    """Make earlier tool calls render as JSON objects in the next prompt. Edits the conversation in place.

    AgentTune keeps each call's arguments as a JSON string and keeps the raw model text as content. The chat
    template then shows the model its own history as "arguments": "{\\"sql\\": ...}" next to a second copy of the
    call, and a small model copies that escaped form, which does not parse (docs/DECISIONS.md, 2026-11-16).
    """
    for m in conversation:
        if m.get("role") == "assistant" and m.get("tool_calls"):
            m["content"] = ""
            for c in m["tool_calls"]:
                f = c.get("function", c)
                if isinstance(f.get("arguments"), str):
                    try:
                        f["arguments"] = json.loads(f["arguments"])
                    except json.JSONDecodeError:
                        pass


def task_id_of(conversation: list[dict]) -> str:
    for m in conversation:
        if m.get("role") == "user":
            found = TASK_ID_RE.search(str(m.get("content", "")))
            if found:
                return found.group(0)
    raise ValueError("no task id in the conversation")


def make_tools(env: SqlEnv) -> list[Callable]:
    def list_tables() -> str:
        """
        List the names of all tables in the database.

        Returns:
            A JSON list of table names.
        """
        out = env.query("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name", None)
        return out if out.startswith(("Error", "The report")) else json.dumps([r[0] for r in json.loads(out)])  # ponytail: prefix check, fine while tool errors all start with these words

    def describe_table(name: str) -> str:
        """
        Show the columns of one table.

        Args:
            name: The table name.

        Returns:
            A JSON list of [column name, column type] pairs.
        """
        if not re.fullmatch(r"\w+", str(name)):
            return "Error: invalid table name."
        out = env.query(f"SELECT name, type FROM pragma_table_info('{name}')", None)
        return "Error: no such table." if out == "[]" else out

    def run_query(sql: str) -> str:
        """
        Run one read-only SQL query on the database and see up to 20 result rows.

        Args:
            sql: The SQLite query to run.

        Returns:
            A JSON list of result rows, or an error message.
        """
        out = env.query(str(sql), env.max_rows)
        return out if out.startswith(("Error", "The report")) else out + NUDGE

    def submit(sql: str) -> str:
        """
        Submit the final SQL query for the report. This ends the task. Call it exactly once.

        Args:
            sql: The SQLite query that answers the question.

        Returns:
            A confirmation message.
        """
        no = env.refuse()
        if no:
            return no
        if env.calls_this_turn > 1:  # the model must have seen its query results before it submits
            return NOT_ALONE
        env.submitted = True
        return SAVED

    return [list_tables, describe_table, run_query, submit]


def _calls(message: dict) -> list[tuple[str, dict]]:
    out = []
    for c in message.get("tool_calls") or []:
        f = c.get("function", c)
        args = f.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {"_raw": args}
        out.append((str(f.get("name")), args if isinstance(args, dict) else {"_raw": args}))
    return out


def episode_from_conversation(conversation: list[dict]) -> Episode:
    """Tool calls in order with their outputs. The first submit call's sql is the submission."""
    calls: list[tuple[str, dict]] = []
    outputs: list[str] = []
    for m in conversation:
        if m.get("role") == "assistant":
            calls += _calls(m)
        elif m.get("role") == "tool":
            outputs.append(str(m.get("content", "")))
    outputs += [""] * (len(calls) - len(outputs))
    tool_calls = tuple(ToolCall(n, a, o) for (n, a), o in zip(calls, outputs))
    # Only an accepted submit counts. AgentTune may wrap the tool output, so match on the confirmation text.
    submitted = next((c.args.get("sql") for c in tool_calls if c.name == "submit" and SAVED in c.output), None)
    return Episode(task_id_of(conversation), tool_calls, None if submitted is None else str(submitted))


def episode_stats(conversation: list[dict], episode: Episode) -> dict[str, int]:
    """steps = assistant turns; tool_errors = tool outputs that report an error or an unknown tool."""
    errors = sum(o.output.startswith("Error") or "error" in o.output[:40].lower() or o.name not in TOOL_NAMES for o in episode.tool_calls)
    return {"steps": sum(m.get("role") == "assistant" for m in conversation), "tool_calls": len(episode.tool_calls), "tool_errors": errors}
