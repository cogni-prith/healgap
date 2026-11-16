"""M0: AgentTune no-GPU quickstart, copied from external/AgentTune/docs/getting-started/quickstart.md lines 7-22."""

from agenttune.agentic import DictToolHarness, Project, ReActStrategy

harness = DictToolHarness({"add": lambda a, b: a + b}, max_steps=4)
strategy = ReActStrategy(
    lambda s: {"name": "add", "arguments": {"a": 2, "b": 3}}
    if s.step == 0
    else {"name": "finish", "arguments": {"answer": "5"}}
)
proj = Project(strategy=strategy, harness=harness)

log = proj.infer("what is 2+3?")
print("infer ->", type(log).__name__, log)
ev = proj.evaluate([{"task": "what is 2+3?", "expected": "5"}])
print("evaluate ->", ev)
ag = proj.evaluate_agentic(["what is 2+3?"])
print("evaluate_agentic ->", ag)
