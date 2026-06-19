# LangGraph Agent — what a framework actually buys you

A ReAct agent built with [LangGraph](https://langchain-ai.github.io/langgraph/)
(the framework that manages an agent loop for you), built specifically to answer
one question with a controlled experiment: **when an agent works better, is it the
framework or the model?**

This is the framework version of a previously hand-built agent loop. Comparing the
two — same task, same model — isolates exactly what LangGraph is and isn't
responsible for.

## What LangGraph is (mapped to a hand-built loop)

LangGraph models an agent as a **graph**: nodes (steps) connected by edges (flow),
all sharing one **State** object that passes through. A ReAct agent is essentially
two nodes with a looping edge:

| LangGraph concept | The hand-built equivalent |
|-------------------|---------------------------|
| "Agent" node (LLM decides) | the `ollama.chat(...)` call |
| "Tools" node (run tools) | the `for call in tool_calls:` block |
| Looping edge (back to LLM) | the `for step in range(max_steps):` loop |
| Shared **State** (`messages`) | the growing `messages` list |
| `create_react_agent(model, tools)` | the entire hand-written agent file |

LangGraph didn't invent new concepts — it gave a hand-written loop a formal
structure (nodes + edges + state) and runs it for you. The prebuilt
`create_react_agent` collapses the whole loop into one function call. Tools are
just plain Python functions; LangGraph reads their name, type hints, and docstring
to build the tool schema automatically (the docstring is load-bearing — the LLM
reads it to decide when to call).

> Note on imports: `create_react_agent` from `langgraph.prebuilt` is the verified
> current v1.0 API. Many tutorials still show deprecated v0.1 patterns
> (`set_entry_point()` etc.). LangGraph reached stable v1.0 in October 2025.

## The experiment: framework vs. model

The hard part of the earlier hand-built agent was **dependent chaining** — "What is
15 plus the current hour?", which requires: call `get_current_time` → extract the
hour from the result → pass it to `add`. The small model `llama3.2` failed this
repeatedly (passing tool *names* as arguments instead of values, fabricating hours,
dumping code). The question: does a framework fix that?

A three-way controlled comparison, holding one variable constant at a time:

| Setup | Dependent chaining result |
|-------|---------------------------|
| Hand-built loop + `llama3.2` | **Fails** (~40 runs; passes tool names as args, fabricates hours) |
| LangGraph + `llama3.2` | **Still fails** — identical failure modes |
| LangGraph + `qwen2.5:7b` | **Works** — 5/5 correct, verified against ground truth |

### What this proves

- **LangGraph + llama failed exactly like the hand loop did.** Automating the loop
  perfectly changed *nothing* about the chaining failure. This isolates the
  variable: the loop mechanics were never the problem.
- **Swapping only the model fixed it completely.** `qwen2.5:7b` ran the full chain
  (`get_current_time` → `20:33:20` → `get_hour_from_time` → `20` → `add(15,20)` →
  `35`) reliably, 5 for 5, and `35` matched the real hour (verified: ~8:30 PM).

> **The framework was never the missing piece — the model was.**
> A framework manages *complexity* (loop, tool execution, history, error recovery);
> it does not add *capability* (the model's reasoning). You need both: the framework
> for the wiring, the right model for the reasoning. They are separate axes.

### What LangGraph *did* improve

Real, but bounded, benefits over the hand-rolled loop:

- The entire agent collapsed to `create_react_agent(model, tools=[...])` — no
  hand-written tool schemas, no `available_tools` dict, no manual loop/step-cap.
- Built-in error recovery: a bad tool call was caught, formatted as a helpful
  message ("Please fix the error and try again"), and fed back to the model
  automatically — more polished than a hand-rolled `try/except`. (It still couldn't
  make `llama3.2` chain — the model's limit, not the loop's.)

## Setup & run

Requires Python 3.10+, Ollama running, and a model pulled
(`ollama pull llama3.2` and/or `ollama pull qwen2.5:7b`).

```bash
pip install langgraph langchain langchain-ollama
python agent.py
```

Swap models by changing the one `ChatOllama(model=...)` line.

## Biggest takeaway

**Frameworks and models are independent axes of improvement.** A framework makes an
agent *easier to build* and manages its complexity; only a more capable model makes
it *smarter*. Conflating the two — switching frameworks hoping for better behavior,
or blaming the model for a loop bug — is a common mistake. Holding each variable
constant in turn ("change the loop, change nothing in behavior; change the model,
fix everything") cleanly separates the two.

## How this fits the series

The fifth from-scratch build, after RAG, MCP, a hand-built agent loop, and an
MCP-consuming agent. Doing the hand-built loop *first* is what makes LangGraph
legible — every node, edge, and state maps onto something written by hand. Use the
easy version, but know exactly what it's hiding.