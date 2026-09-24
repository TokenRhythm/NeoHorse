<div align="center">
  <h1>NeoHorse-Jev</h1>
  <p><b>Prefill-only decisions for agent workflows.</b></p>
</div>

<div align="center">
  <a href="https://github.com/TokenRhythm/NeoHorse"><img alt="GitHub" src="https://img.shields.io/badge/GitHub-NeoHorse-181717?logo=github&logoColor=white"></a>
  <a href="https://huggingface.co/collections/TokenRhythm/neohorse-jev"><img alt="Hugging Face" src="https://img.shields.io/badge/Hugging%20Face-Models-FFD21E?logo=huggingface&logoColor=000000"></a>
  <a href="https://www.modelscope.cn/models/TokenRhythm/NeoHorse-Jev-4B"><img alt="ModelScope" src="https://img.shields.io/badge/ModelScope-Models-624AFF?logo=modelscope&logoColor=white"></a>
  <a href="https://tokenrhythm.ai/"><img alt="Company" src="https://img.shields.io/badge/Company-TokenRhythm-F97316?logo=homeassistant&logoColor=white"></a>
  <a href="https://x.com/opensquilla"><img alt="Twitter / X" src="https://img.shields.io/badge/Twitter%20%2F%20X-OpenSquilla-111827?logo=x&logoColor=white"></a>
  <a href="https://github.com/TokenRhythm/NeoHorse/blob/main/jev/LICENSE"><img alt="License: Apache-2.0" src="https://img.shields.io/badge/License-Apache--2.0-64748B"></a>
</div>

<div align="center"><a href="DEPLOYMENT.md">Deployment</a></div>

## Introduction

We introduce **NeoHorse-Jev-4B**, a **4B structured decision model** from TokenRhythm, built on [NeoHorse-1-4B](https://huggingface.co/TokenRhythm/NeoHorse-1-4B). Given a state and questions defined by your application, it predicts decisions and their probabilities for routing requests, selecting tools, checking conditions, and rating outcomes.

The model uses **prefill-only inference** with three decision types: **Choice**, **Noul**, and **Score**. It predicts directly over the answers you define, without autoregressive text generation.

**NeoHorse-Jev-4B scores 77.70 on the six-group text aggregate below, the highest among the four open-weight decision models with complete results in this comparison.** It also achieves **83.26% mean accuracy** across Nimble, VitaminC, and MASSIVE, **11.50 percentage points** above the NeoHorse-1-4B baseline.

- **Application-defined decisions.** Define candidate actions, yes/no questions, or ordered rating levels. Text requests can include multiple questions.
- **Probabilities for application logic.** Use candidate distributions, yes/no probabilities, and expected ratings to drive routing rules and thresholds.
- **Local deployment.** Run with vLLM, SGLang, or the native Python, CLI, and HTTP runtime. Optional image requests combine a single image with text.

## Decision Demos

![NeoHorse-Jev-4B six-demo grid](assets/jev-six-demo-grid.gif)

**Six decision demos:** Tetris, Snake, robot manipulation, Mahjong, four-player bomb arena, and autonomous driving (left to right, top to bottom). Each panel preserves the original replay and decision displays and loops independently.

## Evaluation

Results updated **September 24, 2026**. These are our evaluations under the protocols described below. Text accuracy, image understanding, and interactive games are reported separately.

### Text Decision Benchmarks

All component scores are on a 0–100 scale; higher is better. NeoHorse-Jev-4B uses the **vLLM** results for JevBench, Kev, and OpenJev in this table; Nimble, VitaminC, and MASSIVE retain the original fixed-subset evaluation results.

| Model | JevBench | Kev | OpenJev text | Nimble | VitaminC | MASSIVE | AVG |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | **77.13** | 77.87 | **65.39** | <ins>80.50</ins> | 68.28 | 84.86 | <ins>75.67</ins> |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | 73.71 | <ins>81.47</ins> | 54.75 | 73.40 | 76.46 | **85.71** | 74.25 |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 55.82 | 61.30 | 40.07 | 45.04 | **78.63** | 68.57 | 58.24 |
| [Laya Typed Decisions](https://huggingface.co/convaiinnovations/laya-typed-decisions) | -- | -- | -- | 48.94 | <ins>78.30</ins> | 65.43 | -- |
| **[NeoHorse-1-4B](https://huggingface.co/TokenRhythm/NeoHorse-1-4B)** | -- | -- | -- | 69.15 | 63.27 | 82.86 | -- |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | <ins>75.73</ins> | **81.92** | <ins>58.74</ins> | **87.23** | 77.13 | <ins>85.43</ins> | **77.70** |

**Bold scores** mark the best result and <ins>underlined scores</ins> the second-best among the listed open-weight entries. `--` means no result is available. NeoHorse-1-4B is a base-model reference; missing groups are not filled with zeros or results from a different checkpoint.

**AVG** is our equal-weight mean of the six displayed group scores, calculated before rounding the final aggregate. It is not pooled per-example accuracy or an official combined leaderboard. Only models with all six groups are ranked by this aggregate; images and games do not enter it.

NeoHorse-Jev-4B leads the tested open-weight entries on **Kev (81.92)** and **Nimble (87.23)**. Open-Jev-9B scores higher on JevBench and OpenJev's static text tasks; Kev-4B scores slightly higher on MASSIVE, and the Laya checkpoints score higher on VitaminC. The aggregate advantage therefore reflects the balance across tasks, rather than a win on every benchmark.

<details>
<summary>Benchmark scope, sample counts, and aggregation</summary>

| Benchmark group | Evaluated scope | Score used in the overview |
| --- | --- | --- |
| JevBench | Public set of 231 examples | Official family-macro score |
| Kev | Development and test splits of decision-v7, transfer-v4, and transfer-v9; 6,436 input records in total | Equal-weight mean of the six clean-accuracy scores; a record may contain multiple decisions |
| OpenJev text | Static text tasks: NLI, multiple-choice reranking, and fixed-candidate GSM8K | Equal-weight mean of 19 task scores; the two MNLI splits are averaged first |
| Nimble | 282 examples selected from 324, keeping related case groups intact; 116 Choice, 112 Noul, 54 Score | Per-example exact decision accuracy, including exact rating-level matches |
| VitaminC-dev | 599 examples from the upstream Nimble sampling pipeline | Three-way evidence/claim classification accuracy |
| MASSIVE-en | 350 English test examples from the upstream Nimble sampling pipeline | Classification accuracy across 18 assistant scenarios; not intent/slot or multilingual evaluation |

For Nimble, VitaminC, and MASSIVE, selected IDs and records were frozen before model comparison. Reference answers are used for scoring, not as model input. Upstream VitaminC/MASSIVE sampling uses seed `20260918` and complete case groups. Local selection uses a 384-token state limit, a 2,048-token packed decision limit, and at most 26 candidates; the base-model letter-logit prompt allows 4,096 tokens. These are subset-selection rules for these three datasets, not universal limits for all benchmarks or deployment. Nimble falls from 324 to 282 examples after length and whole-group filtering; the other two subsets pass unchanged.

</details>

<details>
<summary>Nimble, VitaminC, and MASSIVE: three-benchmark means</summary>

| Model | Three-benchmark mean accuracy (%) |
| --- | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | 77.88 |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | <ins>78.53</ins> |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 64.08 |
| [Laya Typed Decisions](https://huggingface.co/convaiinnovations/laya-typed-decisions) | 64.22 |
| **[NeoHorse-1-4B](https://huggingface.co/TokenRhythm/NeoHorse-1-4B)** | 71.76 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | **83.26** |

This mean weights Nimble, VitaminC, and MASSIVE equally, rather than pooling their 1,231 examples. The three-benchmark means retain the original evaluation report, which averages unrounded accuracies; recomputing from the two-decimal component scores can differ by 0.01. For example, Kev is reported as 78.53. The separately defined AVG above uses the six displayed group scores.

</details>

<details>
<summary>Detailed text comparisons: JevBench, Kev, and OpenJev</summary>

**JevBench.** NeoHorse-Jev-4B has 75.32% per-example accuracy and 100% valid output format on the public 231 examples. Its 75.73 family-macro score weights families, rather than individual examples.

| Model | adequacy | adversarial | ambiguous | extraction | fact | intent |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | **83.33** | **100.00** | 42.86 | 91.67 | **100.00** | **100.00** |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | 66.67 | **100.00** | <ins>57.14</ins> | <ins>95.83</ins> | **100.00** | <ins>95.83</ins> |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 66.67 | <ins>50.00</ins> | 14.29 | 83.33 | <ins>83.33</ins> | 83.33 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | <ins>75.00</ins> | **100.00** | **71.43** | **100.00** | **100.00** | **100.00** |

| Model | judge_hard | long_policy | multi_hop | ordinal | policy | probability |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | **76.47** | **47.37** | **66.67** | **100.00** | **100.00** | **60.00** |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | <ins>52.94</ins> | <ins>21.05</ins> | <ins>55.56</ins> | **100.00** | <ins>91.67</ins> | <ins>50.00</ins> |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 41.18 | <ins>21.05</ins> | 33.33 | <ins>91.67</ins> | 83.33 | <ins>50.00</ins> |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | <ins>52.94</ins> | **47.37** | <ins>55.56</ins> | **100.00** | **100.00** | 40.00 |

| Model | routing | routing_hard | temporal_numeric | tool_selection | tradeoff | trap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | <ins>66.67</ins> | **100.00** | <ins>20.00</ins> | **100.00** | <ins>33.33</ins> | **100.00** |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | **100.00** | **100.00** | 6.67 | **100.00** | <ins>33.33</ins> | **100.00** |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 50.00 | <ins>20.00</ins> | **33.33** | **100.00** | **100.00** | 0.00 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | **100.00** | **100.00** | 0.00 | **100.00** | <ins>33.33</ins> | <ins>87.50</ins> |

Examples: adequacy: 12; adversarial: 6; ambiguous: 7; extraction: 24; fact: 12; intent: 24; judge_hard: 17; long_policy: 19; multi_hop: 18; ordinal: 12; policy: 12; probability: 10; routing: 12; routing_hard: 5; temporal_numeric: 15; tool_selection: 12; tradeoff: 6; trap: 8.

**Kev.** Clean accuracy (%) by suite; record counts differ from decision counts.

| Model | decision-v7 / development | decision-v7 / test | transfer-v4 / development | transfer-v4 / test | transfer-v9 / development | transfer-v9 / test |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | 80.30 | 77.00 | 77.44 | 83.54 | 72.47 | <ins>76.48</ins> |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | **87.18** | **87.08** | <ins>79.73</ins> | <ins>83.69</ins> | <ins>74.76</ins> | 76.39 |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 66.22 | 65.50 | 65.09 | 65.55 | 52.39 | 53.06 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | <ins>86.23</ins> | <ins>86.58</ins> | **81.71** | **84.60** | **75.53** | **76.86** |

Input records: decision-v7 / development: 1,204; decision-v7 / test: 1,176; transfer-v4 / development: 764; transfer-v4 / test: 764; transfer-v9 / development: 1,264; transfer-v9 / test: 1,264.

**OpenJev static text.** NLI classification accuracy (%):

| Model | scitail | anli_r1 | anli_r2 | anli_r3 | wanli | control |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | 79.16 | **74.00** | **66.30** | **59.42** | **67.10** | **67.58** |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | <ins>84.81</ins> | 65.60 | 54.30 | 52.25 | 63.50 | 64.35 |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 74.84 | 48.40 | 38.80 | 34.33 | 53.00 | 37.64 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | **87.02** | <ins>67.20</ins> | <ins>56.20</ins> | <ins>53.42</ins> | <ins>65.74</ins> | <ins>65.96</ins> |

| Model | MNLI / validation_matched | MNLI / validation_mismatched |
| --- | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | 80.64 | 80.54 |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | **89.17** | <ins>89.35</ins> |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 63.28 | 64.27 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | <ins>88.95</ins> | **89.46** |

Examples: scitail: 2,126; anli_r1: 1,000; anli_r2: 1,000; anli_r3: 1,200; wanli: 5,000; control: 805; MNLI / validation_matched: 9,815; MNLI / validation_mismatched: 9,832.

Multiple-choice rerank accuracy:

| Model | arc_easy | arc_challenge | winogrande | gsm8k_mc4 | gsm8k_mc10 | gpqa |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | **95.71** | **87.29** | **66.30** | **52.69** | **35.71** | **37.37** |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | 75.42 | 66.89 | 58.33 | 38.59 | 20.77 | 33.84 |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 40.19 | 33.36 | 49.64 | 24.26 | 8.49 | 26.77 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | <ins>88.93</ins> | <ins>78.50</ins> | <ins>60.69</ins> | <ins>41.77</ins> | <ins>21.83</ins> | <ins>34.34</ins> |

| Model | gpqa_fewshot | chess | hellaswag | mmlu | mmlu_fewshot |
| --- | ---: | ---: | ---: | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | **39.90** | **52.40** | **54.09** | **66.80** | **65.05** |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | <ins>34.85</ins> | 19.20 | 18.92 | 52.29 | 57.50 |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 22.22 | <ins>29.60</ins> | 28.44 | 29.96 | 26.58 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | 34.34 | 22.00 | <ins>34.95</ins> | <ins>59.19</ins> | <ins>60.20</ins> |

Examples: arc_easy: 2,376; arc_challenge: 1,172; winogrande: 1,267; gsm8k_mc4: 1,319; gsm8k_mc10: 1,319; gpqa: 198; gpqa_fewshot: 198; chess: 500; hellaswag: 10,042; mmlu: 14,042; mmlu_fewshot: 14,042.

**GSM8K with frozen candidates (200 examples).** The main metric is `nli_rerank@4`:

| Model | nli_rerank@4 | nli_rerank_margin@4 |
| --- | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | **95.00** | **95.00** |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | 89.50 | 89.50 |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 91.00 | 91.50 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | <ins>94.50</ins> | <ins>94.00</ins> |

Examples: nli_rerank@4: 200; nli_rerank_margin@4: 200.

The shared candidate set has 93.00% greedy accuracy, 93.50% majority-vote accuracy, and a 97.00% oracle@4 ceiling. These are properties of the same candidate pool, not separate generations by each decision model. The 19-task aggregate uses the main rerank score, not the auxiliary margin score.

</details>

### Image and Text Evaluation

On **Image-NLI**, NeoHorse-Jev-4B reaches **60.65% accuracy over 8,000 examples** with vLLM; the native runtime gives 60.66%. The task evaluates statements against an image and text context.

| Model | Overall | `vqa_answer` | `vqa_answer_neg` | `vqa_disagree` | `vqa_spatial` | `vqa_yesno` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)**<br>vLLM | 60.65 | 75.94 | 68.79 | 52.88 | 59.95 | 48.53 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)**<br>Native | 60.66 | 75.94 | 68.63 | 52.98 | 60.03 | 48.37 |

Examples: Overall: 8,000; `vqa_answer`: 1376; `vqa_answer_neg`: 644; `vqa_disagree`: 1040; `vqa_spatial`: 3648; `vqa_yesno`: 1292.

The comparison report contains no Image-NLI results for Kev-4B, Open-Jev-9B, or Laya, so this is a capability measurement without a cross-model ranking. The image assets were reconstructed and frozen locally; this does not claim reproduction of the upstream author's unavailable original image assets.

<details>
<summary>Doom with image input: all 11 candidate configurations</summary>

| Model | `action` | `danger` | `pixels` | `pixels_pct` | `pixels_sym` | `precise` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)**<br>vLLM | 1.00 | 1.40 | 9.20 | 7.40 | 8.40 | 16.00 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)**<br>Native | 1.00 | 1.40 | 11.80 | 8.80 | 10.00 | 15.60 |

| Model | `should` | `thirds` | `where` | `where_closest` | `where_plain` |
| --- | ---: | ---: | ---: | ---: | ---: |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)**<br>vLLM | 1.00 | 12.80 | 1.40 | 1.40 | 6.00 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)**<br>Native | 1.00 | 10.60 | 1.40 | 1.40 | 8.40 |

Each configuration runs for five episodes; scores are mean kills. Five author configurations (`pixels`, `pixels_sym`, `precise`, `thirds`, `where_closest`) use the completed reruns; the six unchanged configurations retain their valid results. The report supplies no image-interface results for the comparison models. All configurations are listed because candidate wording substantially affects the outcome.

</details>

### Interactive Decision Tasks

The September 24 results include the completed game reruns and corrected Minecraft action execution. The tables below report the specified candidate configurations separately and use vLLM for NeoHorse-Jev-4B unless another backend is named. **Text-state Doom, Flappy, and Minecraft results are not image-input evaluations.** Game scores use their own units and are excluded from the text aggregate.

<details>
<summary>Cross-model game results: Doom, Flappy, and Minecraft</summary>

**Doom with text state — mean kills, five episodes per configuration.**

| Model | `position` (author configuration) | `position_none` (includes no-enemy condition) | `aligned_state` (aligned target and tolerance) |
| --- | ---: | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | 11.20 | 7.80 | 18.60 |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | 1.40 | 10.40 | 14.20 |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 1.00 | 1.60 | 1.00 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | 1.40 | 10.60 | 14.40 |

`aligned_state` changes target definition and tolerance wording, so it is a different decision policy from the author's `position` configuration. The reported environment controls are random: 1.00 and oracle: 16.60 mean kills; five-episode outcomes should not be read as a precise ranking.

**Flappy — mean pipes cleared.** Both NeoHorse-Jev backends are shown because real-time outcomes depend on the deployment path. No best/second-best markers are applied to this timing-dependent table.

| Model | sign (author) | position (author) | action (real-time) | action (wait for model) | position_v (real-time) | position_v (wait for model) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | 28.00 | 23.50 | 0.60 | 0.70 | 8.95 | 48.00 |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | 28.00 | 2.67 | 0.00 | 0.10 | 26.80 | 48.00 |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 19.00 | 0.50 | 0.00 | 0.00 | 0.00 | 0.00 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)**<br>vLLM | 27.67 | 27.67 | 0.05 | 0.05 | 15.35 | 48.00 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)**<br>Native | 28.00 | 27.83 | 0.00 | 0.05 | 42.00 | 48.00 |

Settings: sign (author) and position (author) — 6 episodes, 900-frame cap, 15 FPS; action (real-time) and position_v (real-time) — 20 episodes, 1500-frame cap, 30 FPS; action (wait for model) and position_v (wait for model) — 20 episodes, 1500-frame cap, 0 FPS.

`FPS = 0` waits for every model's response. Flappy outcomes are not a controlled cross-model speed benchmark.

**Real Minecraft — success rate (%), ten episodes and at most 60 decision steps per strategy.**

| Model | flat/action | flat/state | chain |
| --- | ---: | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | 0.00 | 80.00 | 100.00 |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | 0.00 | 60.00 | 90.00 |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 0.00 | 0.00 | 20.00 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | 20.00 | 50.00 | 90.00 |

These use the corrected action cancellation and pathfinding-failure handling, with a 240-second action timeout. `flat/action` is a separate ten-episode run; `flat/state` and `chain` share the corrected execution setup. Native NeoHorse-Jev results are 30.00%, 40.00%, and 90.00%, respectively. The environment oracle itself reaches 70–100% across model runs, while random scores 0%, so environment variation remains relevant.

**Simulated Minecraft — success rate (%), ten episodes and at most 60 decision steps per strategy.**

| Model | flat/action | chain |
| --- | ---: | ---: |
| [Open-Jev-9B](https://huggingface.co/ZefanCai/Open-Jev-9B) | 0.00 | 100.00 |
| [Kev-4B](https://huggingface.co/jaredpalmer/kev-4b) | 0.00 | 100.00 |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 0.00 | 0.00 |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | 0.00 | 100.00 |

The simulated environment's oracle reaches 100% and random scores 0%. Simulated and real Minecraft are different settings and should not be averaged together.

</details>

## Download Model

| Model | Download Links | Parameters | Base Model |
| --- | --- | --- | --- |
| **[NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)** | [🤗 Hugging Face](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B)<br>[🤖 ModelScope](https://www.modelscope.cn/models/TokenRhythm/NeoHorse-Jev-4B) | ~4B | [NeoHorse-1-4B](https://huggingface.co/TokenRhythm/NeoHorse-1-4B) |

Download the complete model bundle, including the backbone, tokenizer, separate decision head, and matching runtime wheel. This GitHub repository provides the inference source, backend adapters, and examples.

<details>
<summary>Model details</summary>

| Field | Value |
| --- | --- |
| Parameters | Approximately 4B |
| Base model | NeoHorse-1-4B |
| Input | Text, or a single image with text |
| Decision types | Choice, Noul, Score |
| Inference | Prefill-only |
| License | Apache-2.0 |

</details>

## Deployment

Choose [vLLM](#vllm), [SGLang](#sglang), or the [native runtime](#native-runtime). Each path requires the complete model bundle from Hugging Face or ModelScope.

Use a separate, existing environment for each backend. The adapters and example requests are maintained in the [GitHub source repository](https://github.com/TokenRhythm/NeoHorse/tree/main/jev). If you have only downloaded the model bundle, obtain the source first:

```bash
git clone https://github.com/TokenRhythm/NeoHorse.git
cd NeoHorse/jev
```

Run the commands below from the `jev/` directory of the cloned NeoHorse repository and replace `/path/to/model` with the complete model directory downloaded from Hugging Face or ModelScope.

### vLLM

Use an existing **vLLM 0.28.0** environment.

```bash
# Start the server and keep this terminal running
CUDA_VISIBLE_DEVICES=0 python infer/vllm/launch.py \
  --bundle /path/to/model --port 30000

# Once ready, run inference from another terminal
python infer/vllm/infer.py \
  --bundle /path/to/model \
  --url http://127.0.0.1:30000 \
  --request infer/request.json
```

### SGLang

Use an existing **SGLang 0.5.17** environment.

```bash
# Start the server and keep this terminal running
CUDA_VISIBLE_DEVICES=0 python infer/sglang/launch.py \
  --bundle /path/to/model --port 30000

# Once ready, run inference from another terminal
python infer/sglang/infer.py \
  --bundle /path/to/model \
  --url http://127.0.0.1:30000 \
  --request infer/request.json
```

The sample request is included. Results are printed to the terminal; read `answers.move.choice` and `answers.move.probabilities`. Both backends also support a single image combined with text. See [infer/README.md](infer/README.md) for text and image examples, dependency setup, and input limits.

### Native Runtime

The `neohorse_decision` package provides local Python and CLI inference, plus HTTP services for text and image decisions. Expand the walkthrough for installation and examples of all three decision types, or see the [Deployment](DEPLOYMENT.md) guide for the complete API reference.

<details>
<summary>Installation and usage examples</summary>

#### 1. Download the Complete Model Release

Download the complete release from [Hugging Face](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B/tree/main) or [ModelScope](https://www.modelscope.cn/models/TokenRhythm/NeoHorse-Jev-4B), then set its local path:

```bash
export MODEL_DIR="/path/to/NeoHorse-Jev-4B"
cd "$MODEL_DIR"
```

The complete model bundle contains:

| File or directory | Purpose |
| --- | --- |
| `backbone/` | Unified multimodal backbone; language and vision parameters share safetensors shards and an index |
| `tokenizer/` | Matching tokenizer |
| `pointer_head.safetensors` | Separate decision head |
| `model_manifest.json` | Model composition and provenance |
| `dist/`, `package/` | Runtime wheel and source |
| `example_request.json` | Example request covering all three decision types |
| `vision/` | Local image inference and HTTP image client examples |

Use the matching `neohorse_decision` package for the native runtime. The vLLM and SGLang adapters are in `jev/infer/` in this repository; see [backend deployment](#vllm) above. All three paths require the complete model directory, including the separate decision head.

#### 2. Install the Runtime

The recorded test environment is **Linux, Python 3.12, PyTorch 2.8.0, Transformers 5.17.0, Triton 3.7.1, and flash-linear-attention 0.5.2**, with a CUDA GPU that supports BF16. See [environment.json](https://www.modelscope.cn/models/TokenRhythm/NeoHorse-Jev-4B/file/view/master/environment.json) and [DEPLOYMENT.md](DEPLOYMENT.md) for details.

The following commands assume these ML dependencies are already installed in an isolated environment and GPU 0 has been allocated to your workload:

```bash
python -m pip install --no-deps dist/neohorse_decision-1.0.0-py3-none-any.whl
python -m pip install 'fastapi==0.141.1' 'uvicorn==0.53.0' 'starlette==1.6.0' 'httpx==0.28.1' 'pillow==12.3.0'

CUDA_VISIBLE_DEVICES=0 neohorse-decision predict --model-dir . --request example_request.json
```

`--no-deps` installs the bundled wheel into an already prepared environment; it does not install the ML dependencies listed above. The unified backbone weights occupy approximately 9.08 GB. Actual GPU memory usage also depends on input and runtime settings. **Download the complete model repository and install its bundled runtime.**

#### Decision Types

| Type | Input | Output | Typical use cases |
| --- | --- | --- | --- |
| **Choice** | An ordered dictionary of candidate keys and descriptions | Selected candidate and full candidate probability distribution | Request routing, tool selection, action selection |
| **Noul** | A yes/no question | Probability that the statement is true, `P(true)` | Condition checks, filtering, workflow gates |
| **Score** | Rating levels ordered from lowest to highest | Probability distribution over levels and the expected rating | Quality assessment, severity, priority |

Score levels are indexed from `0`, and the expected rating can be fractional. These use cases describe the interface; performance should be validated on your target tasks.

#### 3. Python Examples

**Provide a state and get a yes/no probability, a selected candidate, or a rating.** The examples below use the same user message to demonstrate the three decision modes.

Load the model once, then reuse `engine` and `state`:

```python
import os

from neohorse_decision import DecisionEngine

engine = DecisionEngine(os.environ["MODEL_DIR"])
state = "I was charged twice for the same order. Please refund the extra charge today."
```

All output numbers below are illustrative, not measured results. Actual values depend on the model's predictions.

##### Noul: Is It True?

**Is the user requesting a refund?** Return the probability of "yes", `P(true)`.

```python
result = engine.predict({
    "state": state,
    "questions": {
        "refund": {
            "type": "noul",
            "instructions": "Is the user requesting a refund?",
        },
    },
})
print(result["answers"]["refund"]["noul"])
```

Illustrative output: `0.97` means the model assigns a 97% probability to the user requesting a refund. Your application can use this to enter a refund workflow.

##### Choice: Which One?

**Which team should handle this message?** Select from the candidates and return each candidate's probability.

```python
result = engine.predict({
    "state": state,
    "questions": {
        "team": {
            "type": "choice",
            "instructions": "Which team should handle this message?",
            "criteria": {
                "billing": "Billing, charges, or refunds",
                "technical": "Product failures or technical issues",
                "other": "Other matters",
            },
        },
    },
})
print(result["answers"]["team"]["choice"])
print(result["answers"]["team"]["probabilities"])
```

Illustrative output:

```text
billing
{'billing': 0.96, 'technical': 0.03, 'other': 0.01}
```

Read `billing` to route the message to the billing team.

##### Score: To What Degree?

**How urgent is the request?** Rate it against the levels you define. Levels start at `0`, and the result is their probability-weighted expected value.

```python
result = engine.predict({
    "state": state,
    "questions": {
        "urgency": {
            "type": "score",
            "instructions": "How soon does the user want this resolved?",
            "criteria": ["Can wait", "This week", "Today"],
        },
    },
})
print(result["answers"]["urgency"]["score"])
```

Illustrative output: `1.9` is close to level `2` ("Today"), which your application can use to raise the request's priority.

Save the four Python blocks above, in order, as `quickstart.py`, then run:

```bash
CUDA_VISIBLE_DEVICES=0 python quickstart.py
```

To make all three decisions in one text request, place `refund`, `team`, and `urgency` in the same `questions` dictionary. One request returns three answers. Set decision thresholds using data from your own tasks.

#### 4. Image and Text Decisions

Save a page screenshot as `screenshot.png`. This Choice example identifies the page's current state:

```python
import os

from PIL import Image
from neohorse_decision.vision import VisionDecisionEngine

vision_engine = VisionDecisionEngine(os.environ["MODEL_DIR"])
with Image.open("screenshot.png") as source:
    screenshot = source.convert("RGB")

result = vision_engine.predict({
    "model": "NeoHorse-Jev-4B",
    "state": "Goal: submit the form. Assess the current page screenshot.",
    "questions": {
        "page_status": {
            "type": "choice",
            "instructions": "Which page state does the screenshot show?",
            "criteria": {
                "success": "Submission succeeded",
                "error": "Submission failed or an error is shown",
                "processing": "Submission or loading is in progress",
                "unknown": "Cannot determine the submission status from the screenshot",
            },
        },
    },
}, screenshot)
print(result["answers"]["page_status"]["choice"])
print(result["answers"]["page_status"]["probabilities"])
```

Image requests also support Noul and Score, with one image and one question per request. Examples for all three modes and HTTP image requests are in the [image usage guide](DEPLOYMENT.md#6-image-requests).

#### 5. HTTP Service

Start the service:

```bash
CUDA_VISIBLE_DEVICES=0 neohorse-decision serve --model-dir "$MODEL_DIR" --port 8080
```

From another terminal, send the same Noul question:

```bash
curl -sS http://127.0.0.1:8080/v1/systemone \
  -H 'Content-Type: application/json' \
  -d '{"model":"NeoHorse-Jev-4B","state":"I was charged twice for the same order. Please refund the extra charge today.","questions":{"refund":{"type":"noul","instructions":"Is the user requesting a refund?"}}}'
```

The service binds to `127.0.0.1` by default. For external access, enable Bearer authentication with `NEOHORSE_API_KEY` and use a TLS gateway. The native endpoint is `/v1/decision`, the System One-style endpoint is `/v1/systemone`, and `/health` reports readiness.

See the [deployment and API guide](DEPLOYMENT.md) for request formats, response fields, default limits, and error handling.

#### Install from Source

With the ML dependencies above already installed, run this from the `jev/` directory of the NeoHorse source repository:

```bash
cd /path/to/NeoHorse/jev
python -m pip install --no-deps ./package
```

`MODEL_DIR` still points to the complete model bundle downloaded from Hugging Face or ModelScope. Inference source is in `package/src/neohorse_decision/`; image clients and local image examples are in `vision/`.

</details>

## Limitations

- **Decisions can be wrong.** Valid structure and normalized probabilities do not guarantee correct judgments. Missing evidence, candidate descriptions, candidate order, and domain shifts can all affect results.
- **Validate probabilities for your application.** NLL, Brier, and ECE calibration results have not been reported. Set thresholds on an independent dataset.
- **Scope claims to measured evidence.** Comprehensive evaluations of multilingual inputs, long inputs, and computational isolation between questions are not yet available. Multiple questions in one request do not imply a single shared forward pass.
- **Applications enforce execution constraints.** Tool permissions, business rules, and action validation remain the application's responsibility. The current materials do not provide latency, GPU memory, or cost comparisons under a common timing protocol.

## License and Acknowledgments

NeoHorse-Jev-4B is released under **Apache License 2.0**. It is derived from NeoHorse-1-4B, whose upstream base is Qwen3.5-4B. Bundled third-party runtime components retain their licenses and attribution. Preserve the relevant copyright, license, and modification notices when redistributing.

We thank Jared Palmer for open-sourcing [Kev](https://github.com/jaredpalmer/kev). Parts of this project's decision inference code are adapted from Kev.

For questions or bug reports, use the [NeoHorse issue tracker](https://github.com/TokenRhythm/NeoHorse/issues).
