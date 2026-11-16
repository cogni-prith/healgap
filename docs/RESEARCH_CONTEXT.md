# Research context

Last literature check: 2026-11-15. Re-check arXiv for concurrent work before submitting. This area moves weekly, and one directly relevant paper appeared this month.

## Research question

When a self-healing loop retrains a tool-using agent using only what its failure detector flags, does the population of reward hacks shift toward hacks the detector misses? Concretely: does the detector-reported hack rate fall across heal rounds while the true hack rate (measured by a hidden checker) stays flat or rises?

Second question: does replacing the hackable reward with an isomorphic reward remove both detected and undetected hacks, with no detector involved?

## Novelty verdict

Short version: the broad phenomenon is established. Our specific setting is not covered. The contribution is a careful measurement in a new setting, not a new phenomenon. Claims must be scoped accordingly.

### Idea 1 (heal loops select for stealth): open in this specific form

What is already known, so we must not claim it:

| Work | What it shows | What it does not cover |
|---|---|---|
| Baker et al. 2025 (OpenAI), [arXiv 2503.11926](https://arxiv.org/abs/2503.11926) | Putting a CoT monitor into the RL reward gives obfuscated reward hacking under enough optimisation. | They note that patching only monitor-flagged bugs is a weak selection pressure toward unflagged hacks, and say they had no empirical evidence of that effect. |
| Taufeeque et al. 2026, Obfuscation Atlas, [arXiv 2602.15515](https://arxiv.org/abs/2602.15515) | Training against a deception probe in a coding RLVR task yields obfuscated policies or obfuscated activations unless KL and penalty are high enough. | Single-turn coding. Penalty in the reward only. |
| "Designing Effective Monitor-Based Interventions for Mitigating Reward Hacking During RL", [arXiv 2611.09828](https://arxiv.org/abs/2611.09828) (Nov 2026) | Qwen3-4B with GRPO on three single-response environments. Compares penalty and screening (dropping flagged rollouts), probes and LLM judges, simulated monitors with random label flips. Models evade naive monitors. Screening removed probe representation drift but not semantic evasion. | No multi-turn tool use. No multi-round retraining loop. No corrective-data SFT. No deployment gate. |
| "Monitor Evasion Depends on What RL Finds and What Monitors Miss", [LessWrong, Nov 2026](https://www.lesswrong.com/posts/moDKmh4GerCjfB5mM/monitor-evasion-depends-on-what-rl-finds-and-what-monitors) | Toy transformers and Qwen3-1.7B. The model moves toward hacks the monitor already missed, and whether it does depends on how common those hacks are before RL. | Arithmetic with a single exploit token. No tools, no heal loop, no gate. |
| "The Verification Horizon", [arXiv 2606.26300](https://arxiv.org/abs/2606.26300) | A closed loop on SWE-Bench: review trajectories each interval, add new hack patterns to the monitor, penalise in the next RL round. | Its hack rate counts only monitor-triggered trajectories. It has no measurement of hacks that evade the monitor. |
| Anthropic GRAFT, [alignment blog 2026](https://alignment.anthropic.com/2026/graft/) | States that penalising with monitors can teach undetectable hacks, and proposes localising hacking into a removable adapter instead. | A different mitigation. Useful as related work. |
| Thaman 2026, Reward Hacking Benchmark, [arXiv 2605.02964](https://arxiv.org/abs/2605.02964) | RL post-training is associated with more reward hacking in multi-step tool use. Hacking rises when honest solutions get hard. | Evaluation of existing models, no training loop. |

What remains open, and is our contribution:

1. **The heal-loop channel.** Prior work applies the monitor as a reward penalty or as rollout screening inside one RL run. A self-healing loop applies selection differently: through which failures get corrective data, which passing trajectories are kept as positives, and which candidate checkpoint the gate deploys. Nobody has measured stealth selection through these channels across rounds.
2. **Multi-turn tool-using agents.** The controlled studies above are single-response.
3. **Reported versus true hack rate, tracked per round.** The one closed-loop paper reports only monitor-triggered hacks. We track both with a hidden checker.
4. **Systematic versus random detector misses at matched recall,** inside a heal loop. The LessWrong result predicts stealth shift only when misses are systematic. We test that prediction in an agent setting.

Honest risk to novelty: 2611.09828 is close in spirit and uses a similar model size. Our difference is the loop form and the agent setting. If a multi-round, agentic version of that paper appears before submission, we cite it and narrow to whatever is still distinct.

### Idea 2 (isomorphic reward): the technique is not new, the application is

- Isomorphic Perturbation Testing: Helff et al. 2026, [arXiv 2604.15149](https://arxiv.org/abs/2604.15149). Single-turn inductive reasoning. Training with isomorphic verification removed the shortcut. The authors point to agentic settings as a possible extension.
- Test-suite accuracy for text-to-SQL: Zhong, Yu, Klein 2020, [arXiv 2010.02840](https://arxiv.org/abs/2010.02840). Checking a predicted query on many databases is a standard evaluation idea in SQL.
- A 2026 survey of agentic reward hacking lists metamorphic tests and hidden tests as known mitigations for verifier gaming: [Springer](https://link.springer.com/article/10.1007/s44163-026-01980-z).

So we present idea 2 as the fix arm, with this framing: a detector-free repair for a heal loop, compared directly against detector-based repair in the same environment. We do not claim to have invented isomorphic or multi-database verification.

## Hypotheses (written before any run, do not edit after results)

- **H1 (stealth shift).** With a detector that has a systematic blind spot, used for filtering plus corrective SFT or for gating, the undetected hack rate U rises across heal rounds or stays flat while the reported hack rate falls.
- **H2 (blind spot matters).** With a simulated detector of the same overall recall but random misses, U does not rise. Hacking falls roughly in proportion across exploit types.
- **H3 (channel comparison, exploratory).** The size of the stealth shift differs by how the detector is used: reward penalty, filter plus corrective SFT, gate only. No predicted ordering.
- **H4 (isomorphic fix).** Switching the retraining reward to the isomorphic reward in the final round lowers the true hack rate across all exploit types, including those the detector misses, without lowering true task success.
- **H5 (discoverability, from prior work).** Stealth shift appears only if the stealthy exploit types already occur at a non-trivial base rate before training. Experiment 0 measures this.

Each hypothesis can fail. A clean failure of H1 is reportable: "heal loops with filter or gate usage did not select for stealth in this setting, unlike reward penalties".

## What we may and may not claim

May claim, if the data supports it:

- A measurement of reported versus true hack rate across heal rounds in a multi-turn SQL agent, for N seeds, on one small open model.
- A comparison of detector usage channels and of systematic versus random misses.
- That an isomorphic reward did or did not repair hacking in this environment.

May not claim:

- That training against monitors causes evasion as a new finding. It is prior work.
- Anything about frontier models, natural (unplanted) loopholes, or production pipelines. Our loopholes are planted and our model is small.
- That isomorphic verification is our method.
- Emergent misalignment effects. Small models show weak effects there (School of Reward Hacks, [arXiv 2508.17511](https://arxiv.org/abs/2508.17511)), and it is out of scope.

## Known threats to validity (address each in the report)

- **Planted loopholes.** The exploit ladder is designed by us. State this plainly. The graded-subtlety design is the point, since small models tend to find only crude hacks on their own (see [this small-scale GRPO study](https://www.lesswrong.com/posts/NzzmNREX4qR54q33j/linear-probes-add-little-for-verifiable-reward-hacking)).
- **Hack versus honest mistake.** "Passes weak verifier, fails ground truth" also catches lucky wrong queries. The oracle labeller separates exploit types from plain errors. Report both.
- **Seeding.** If Experiment 0 shows stealthy exploits never occur at baseline and we add hints to make them discoverable, that is an intervention. Report results with and without it.
- **Small scale.** One model family, few seeds, short training. Report confidence intervals and do not over-read small differences.
- **Detector choice.** Results depend on the specific blind spot. The simulated random-miss detector is the control for this.

## Related work to cite in the report

In addition to the table above: Anthropic, natural emergent misalignment from reward hacking ([blog](https://www.anthropic.com/research/emergent-misalignment-reward-hacking)); recontextualization, [arXiv 2512.19027](https://arxiv.org/abs/2512.19027); CHERRL, [arXiv 2606.04923](https://arxiv.org/abs/2606.04923); AgentDebug, [arXiv 2509.25370](https://arxiv.org/abs/2509.25370); training on documents about monitoring, [arXiv 2605.15257](https://arxiv.org/abs/2605.15257); AgentTune ([GitHub](https://github.com/Lexsi-Labs/AgentTune)).
