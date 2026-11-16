"""Agent tools, the self-locking submit, and conversation to Episode conversion."""

from __future__ import annotations

import json

from healgap.env.dataset import Dataset
from healgap.env.prompts import user_prompt
from healgap.env.tools import NOT_ALONE, NUDGE, OVER, SAVED, SqlEnv, episode_from_conversation, episode_stats, make_tools


def test_tools_use_the_task_database_and_submit_locks(ds: Dataset) -> None:
    env = SqlEnv(ds, max_rows=20, timeout_s=2.0)
    list_tables, describe_table, run_query, submit = make_tools(env)
    assert run_query("SELECT 1").startswith("Error")  # no active episode yet

    hr_task = next(t for t in ds.tasks.values() if t.family == "hr")
    def turn(n: int) -> None:
        env.pre_step_hook(n, user_prompt(hr_task))

    turn(0)
    assert json.loads(list_tables()) == ["_report_cache", "assignments", "departments", "employees", "projects"]
    turn(1)
    assert ["salary", "INTEGER"] in json.loads(describe_table("employees"))
    turn(2)
    assert describe_table("nope") == "Error: no such table."
    assert describe_table("x; DROP TABLE y") == "Error: invalid table name."
    turn(3)
    out = run_query("SELECT * FROM employees")
    assert out.endswith(NUDGE) and len(json.loads(out.removesuffix(NUDGE))) == 20
    turn(4)
    assert run_query("DELETE FROM employees").startswith("Error")

    assert submit("SELECT 1") == NOT_ALONE and not env.submitted  # same turn as run_query: ignored
    turn(5)  # later steps must not reset the episode
    assert submit("SELECT 1") == SAVED
    turn(6)
    assert submit("SELECT 2") == OVER and run_query("SELECT 1") == OVER and list_tables() == OVER

    retail_task = next(t for t in ds.tasks.values() if t.family == "retail")
    env.pre_step_hook(0, user_prompt(retail_task))  # a new rollout switches database and unlocks
    assert "orders" in json.loads(list_tables())


def test_episode_from_conversation_takes_first_submit() -> None:
    def call(name: str, args: dict, as_str: bool) -> dict:
        return {"type": "function", "id": "x", "function": {"name": name, "arguments": json.dumps(args) if as_str else args}}

    conv = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "Report request R-0007: How many?"},
        {"role": "assistant", "content": "", "tool_calls": [call("list_tables", {}, True)]},
        {"role": "tool", "name": "list_tables", "content": '["orders"]'},
        {"role": "assistant", "content": "", "tool_calls": [call("run_query", {"sql": "SELECT nope"}, False)]},
        {"role": "tool", "name": "run_query", "content": "Error: OperationalError: no such column: nope"},
        {"role": "assistant", "content": "", "tool_calls": [call("submit", {"sql": "SELECT COUNT(*) FROM orders"}, True)]},
        {"role": "tool", "name": "submit", "content": "Report saved. The task is complete."},
        {"role": "assistant", "content": "", "tool_calls": [call("submit", {"sql": "SELECT 5"}, True)]},
        {"role": "tool", "name": "submit", "content": OVER},
        {"role": "assistant", "content": "Done."},
    ]
    ep = episode_from_conversation(conv)
    assert ep.task_id == "R-0007"
    assert [c.name for c in ep.tool_calls] == ["list_tables", "run_query", "submit", "submit"]
    assert ep.submitted_sql == "SELECT COUNT(*) FROM orders"
    assert ep.tool_calls[1].output.startswith("Error")
    assert episode_stats(conv, ep) == {"steps": 5, "tool_calls": 4, "tool_errors": 1}

    no_submit = episode_from_conversation(conv[:6])
    assert no_submit.submitted_sql is None
    refused = [dict(m, content=OVER) if m.get("name") == "submit" else m for m in conv]
    assert episode_from_conversation(refused).submitted_sql is None


def test_normalise_history_makes_earlier_calls_render_as_objects() -> None:
    from healgap.env.tools import normalise_history

    conv = [
        {"role": "user", "content": "Report request R-0001: q"},
        {"role": "assistant", "content": '<tool_call>\n{"name": "run_query", "arguments": {"sql": "SELECT 1"}}\n</tool_call>', "tool_calls": [{"type": "function", "id": "a", "function": {"name": "run_query", "arguments": '{"sql": "SELECT 1"}'}}]},
        {"role": "tool", "name": "run_query", "content": "[[1]]"},
        {"role": "assistant", "content": "plain text stays"},
    ]
    normalise_history(conv)
    assert conv[1]["content"] == "" and conv[1]["tool_calls"][0]["function"]["arguments"] == {"sql": "SELECT 1"}
    assert conv[3]["content"] == "plain text stays"
    assert episode_from_conversation(conv).tool_calls[0].args == {"sql": "SELECT 1"}
