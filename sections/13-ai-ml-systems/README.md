# §13 AI and ML Systems

> Required at AI labs, increasingly asked elsewhere.

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `13.01` **[P1]** How transformers work at a systems level: tokens, context window, attention cost
- [ ] `13.02` **[P1]** Inference serving: batching (static, dynamic, continuous), KV cache, streaming, time-to-first-token vs throughput
- [ ] `13.03` **[P1]** Building on LLM APIs: tool use, structured output, retries, cost and latency budgets
- [ ] `13.04` **[P1]** RAG design and its failure modes
- [ ] `13.05` **[P1]** Evaluation: building eval sets, graders, regression detection, offline vs online metrics
- [ ] `13.06` **[P1]** Working effectively with coding agents: task decomposition, verification, knowing when the model is wrong
- [ ] `13.07` **[P2]** Quantization, distillation, speculative decoding
- [ ] `13.08` **[P2]** GPU fundamentals: memory hierarchy, utilization, multi-GPU and multi-node serving
- [ ] `13.09` **[P2]** Agent architecture: planning loops, memory, tool permissions, sandboxing
- [ ] `13.10` **[P2]** Fine-tuning approaches (full, LoRA) and when not to fine-tune
- [ ] `13.11` **[P2]** Training infrastructure basics: data loaders, checkpointing, distributed training

## Layout

```
13-ai-ml-systems/
├── index.html     chapter page (rendered from assets/curriculum.js)
├── concepts/      one HTML page per concept (python tools/new.py concept <topic-id> <slug> "Title")
└── notes.md       your own scratch notes
```

Status: scaffold only. Concept pages and exercises come after chapters 1 and 2.
