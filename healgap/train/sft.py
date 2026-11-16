"""Corrective SFT through AgentTune's create_distill_trainer, with our own trainer_factory.

Why a custom factory (docs/DECISIONS.md, M0 question 4): the built-in one always starts a fresh LoRA and renders
rows without the system prompt or tool schemas. Ours continues from a parent adapter and renders each trajectory
with the tokenizer's chat template, system prompt and tool schemas, so SFT text matches what rollouts see.
"""

from __future__ import annotations

import gc
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from agenttune.agentic import Event, EventKind, EventLog
from agenttune.agentic.distill_trainer import create_distill_trainer
from datasets import Dataset
from peft import LoraConfig, PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.utils import get_json_schema
from trl import SFTConfig, SFTTrainer


@dataclass(frozen=True)
class SftConfig:
    num_train_epochs: float
    learning_rate: float
    batch_size: int
    grad_accum: int
    max_length: int
    lora_r: int
    lora_alpha: int
    lora_dropout: float
    lora_targets: tuple[str, ...]


def to_eventlog(conversation: list[dict]) -> EventLog:
    """Full-tier EventLog for one conversation. The system message is left out; the factory adds it back."""
    log = EventLog(tier="full")
    for m in conversation:
        role = m.get("role")
        if role == "user":
            log.append(Event(EventKind.OBSERVATION, {"text": m["content"]}))
        elif role == "assistant":
            calls = m.get("tool_calls") or []
            if calls:
                log.append(Event(EventKind.TOOL_CALL, {"action": {"tool_calls": calls}}))
            elif m.get("content"):
                log.append(Event(EventKind.TEXT, {"text": m["content"]}))
        elif role == "tool":
            log.append(Event(EventKind.TOOL_RESULT, {"output": m.get("content", "")}))
    return log


_CALL = re.compile(r"^<tool_call>(.*)</tool_call>$", re.S)


def render_messages(row_messages: list[dict], system_prompt: str) -> list[dict]:
    """AgentTune SFT rows -> the message list a rollout produces: system first, one assistant turn per tool round."""
    out: list[dict] = [{"role": "system", "content": system_prompt}]
    for m in row_messages:
        content = m["content"]
        found = _CALL.match(content) if m["role"] == "assistant" else None
        if found:
            content = f"<tool_call>\n{found.group(1)}\n</tool_call>"
        if m["role"] == "assistant" and out[-1]["role"] == "assistant":
            out[-1] = {"role": "assistant", "content": out[-1]["content"] + "\n" + content}  # parallel calls: one turn
        else:
            out.append({"role": m["role"], "content": content})
    return out


class SftFactory:
    """trainer_factory for create_distill_trainer: called as factory(model=, train_dataset=rows, output_dir=, **kw)."""

    def __init__(self, cfg: SftConfig, system_prompt: str, tools: list[Callable], parent_adapter: Path | None, seed: int) -> None:
        self.cfg, self.system_prompt, self.parent, self.seed = cfg, system_prompt, parent_adapter, seed
        self.schemas = [get_json_schema(t) for t in tools]

    def texts(self, rows: list[dict], tok: Any) -> list[str]:
        return [tok.apply_chat_template(render_messages(r["messages"], self.system_prompt), tools=self.schemas, tokenize=False) for r in rows]

    def __call__(self, model: str, train_dataset: list[dict], output_dir: str, **_: Any) -> SftFactory:
        self.model_id, self.rows, self.output_dir = model, train_dataset, output_dir
        return self

    def train(self) -> dict[str, Any]:
        c = self.cfg
        tok = AutoTokenizer.from_pretrained(self.model_id)
        base = AutoModelForCausalLM.from_pretrained(self.model_id, dtype=torch.bfloat16).to("cuda")
        if self.parent is not None:
            model, peft_config = PeftModel.from_pretrained(base, str(self.parent), is_trainable=True), None
        else:
            model, peft_config = base, LoraConfig(r=c.lora_r, lora_alpha=c.lora_alpha, lora_dropout=c.lora_dropout, target_modules=list(c.lora_targets), task_type="CAUSAL_LM")
        args = SFTConfig(output_dir=self.output_dir, num_train_epochs=c.num_train_epochs, learning_rate=c.learning_rate, per_device_train_batch_size=c.batch_size, gradient_accumulation_steps=c.grad_accum, max_length=c.max_length, bf16=True, logging_steps=5, save_strategy="no", report_to="none", seed=self.seed, gradient_checkpointing=True, dataset_text_field="text")
        trainer = SFTTrainer(model=model, args=args, train_dataset=Dataset.from_dict({"text": self.texts(self.rows, tok)}), processing_class=tok, peft_config=peft_config)
        result = trainer.train()
        trainer.save_model(self.output_dir)
        out = {"train_loss": result.training_loss, "steps": result.global_step, "n_rows": len(self.rows), "parent_adapter": None if self.parent is None else str(self.parent)}
        del trainer, model, base
        gc.collect()
        torch.cuda.empty_cache()
        return out


def train_sft(model_id: str, conversations: list[list[dict]], out_dir: Path, system_prompt: str, tools: list[Callable], cfg: SftConfig, parent_adapter: Path | None, seed: int) -> dict[str, Any]:
    """LoRA SFT on the given conversations. Writes the new adapter to out_dir and returns training stats."""
    factory = SftFactory(cfg, system_prompt, tools, parent_adapter, seed)
    trainer = create_distill_trainer(student=model_id, trajectories=[to_eventlog(c) for c in conversations], trainer_factory=factory, output_dir=str(out_dir))
    return trainer.train()
