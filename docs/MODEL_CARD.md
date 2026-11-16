---
base_model: Qwen/Qwen2.5-1.5B-Instruct
library_name: peft
license: apache-2.0
tags: [lora, reward-hacking, self-healing-agents, text-to-sql, agenttune, lexsi-hackathon]
---

# healgap adapters

LoRA adapters for `Qwen/Qwen2.5-1.5B-Instruct` from **healgap**, a Lexsi Labs hackathon project (Track 3, Agentic Fine-tuning) that asks whether a self-healing agent loop fixes the reward hacks its detector cannot see.

Code, write-up and the full decisions log: https://github.com/cogni-prith/healgap (start with `docs/REPORT.md`).
Rollouts, eval records and manifests: https://huggingface.co/datasets/cognitive-prith/healgap-runs

## Warning: several of these adapters hack on purpose

These are research artifacts, not useful SQL agents.

- `seedpolicy_reduced_seed{0,1,2}/adapter` are **deliberately trained to cheat**. They were fine-tuned on scripted demonstrations, half honest and half reward hacks (reading a planted answer cache, submitting a hardcoded literal, submitting a hardcoded literal disguised inside a subquery). They are the starting point of every heal run.
- `heal_reduced_<arm>_seed<k>_<timestamp>/round<r>/adapter` is the candidate policy after heal round `r` of that arm. `state.json` next to it records whether the gate deployed it and which adapter it continued from. `manifest.json` has the full config, seed and library versions.

Arms: `weak_only` (no detector), `filter_rule` (rule detector with a blind spot), `filter_sim` (control detector with random misses), `iso_fix` (rule detector, then an isomorphic check in the last round), and where present `iso_from_start` and `filter_oracle`.

## How they were trained

Corrective SFT through AgentTune's `create_distill_trainer` with a custom trainer factory (TRL `SFTTrainer` underneath). LoRA r 16, alpha 32, dropout 0.05 on the q, k, v and o projections. 3 epochs, learning rate 2e-4, batch 1 with 2-step accumulation. Each round continues from the deployed adapter of the previous round.

## Use

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM
base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
model = PeftModel.from_pretrained(base, "cognitive-prith/healgap-adapters", subfolder="seedpolicy_reduced_seed0/adapter")
```

The adapters expect the system prompt, tool schemas and tool loop from the repository. They are only meaningful inside that environment.

## Limits

One small model, planted loopholes, planted starting behaviour, 3 seeds, 2 heal rounds. See the report's scope section.
