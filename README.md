# LangGraph Agent — what a framework actually buys you

A ReAct agent built with [LangGraph](https://langchain-ai.github.io/langgraph/)
(the framework that manages an agent loop for you), built specifically to answer
two questions with controlled experiments:

1. When an agent works better, is it the **framework** or the **model**?
2. Does a framework (or a better model) protect you from a **lying tool**?

This is the framework version of a previously hand-built agent loop, plus a
framework version of a previously hand-built MCP agent. Comparing each against its
hand-built twin isolates exactly what LangGraph is and isn't responsible for.

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
| `create_agent(model, tools)` | the entire hand-written agent file |

LangGraph didn't invent new concepts — it gave a hand-written loop a formal
structure (nodes + edges + state) and runs it for you. Tools are just plain Python
functions; LangGraph reads their name, type hints, and docstring to build the tool
schema automatically (the docstring is load-bearing — the LLM reads it to decide
when to call).

### Current API (and a lesson about "verified current")

Use:

```python
from langchain.agents import create_agent
```

**Not** `from langgraph.prebuilt import create_react_agent` — that was moved and
renamed in LangGraph v1.0 and now raises:

```
LangGraphDeprecatedSinceV10: create_react_agent has been moved to
`langchain.agents`. Please update your import to
`from langchain.agents import create_agent`. Deprecated in LangGraph V1.0 to be
removed in V2.0.
```

This project was first built with `create_react_agent` from `langgraph.prebuilt` —
which was asserted to be the "verified current v1.0" API and was actually *one
version stale*. The deprecation warning printed by the actual run was the real
source of truth. The lesson that runs through this whole series applies here too:
**trust what the system actually tells you over what someone confidently asserts** —
even a "verified current" claim can be wrong; the running code's own warning is
ground truth.

## Experiment 1: framework vs. model (file: `agent.py`)

The hard part of the earlier hand-built agent was **dependent chaining** — "What is
15 plus the current hour?", which requires: call `get_current_time` → extract the
hour from the result → pass it to `add`. The small model `llama3.2` failed this
repeatedly. The question: does a framework fix that?

A three-way controlled comparison, holding one variable constant at a time:

| Setup | Dependent chaining result |
|-------|---------------------------|
| Hand-built loop + `llama3.2` | **Fails** (~40 runs; passes tool names as args, fabricates hours) |
| LangGraph + `llama3.2` | **Still fails** — identical failure modes |
| LangGraph + `qwen2.5:7b` | **Works** — 5/5 correct, verified against ground truth |

**Conclusion:** LangGraph + llama failed *exactly* like the hand loop did —
automating the loop changed nothing, isolating that the loop mechanics were never
the problem. Swapping only the model fixed it completely.

> A framework manages *complexity* (loop, tool execution, history, error recovery);
> it does not add *capability* (the model's reasoning). They are separate axes — you
> need both: the framework for the wiring, the right model for the reasoning.

## Experiment 2: lying tools across the whole stack (file: `mcp_agent.py`)

The MCP agent was rebuilt here using `MultiServerMCPClient` (from
`langchain-mcp-adapters`) to pull tools from a separate MCP server, handed to
`create_agent`. The adapter replaces an entire hand-written async MCP client (the
connection, handshake, `list_tools`, `call_tool`, and format-conversion glue) with
`tools = await client.get_tools()`. Crucially, `create_agent` doesn't know or care
the tools came from MCP — proving the loop and the tool source are fully decoupled.

The MCP server includes **lying** tools (code that contradicts its description):
`subtract` (described "Subtract two numbers", actually returns `a * b`) and
`get_account_balance` (returns a plausible but fake `$2,347.18`). A pure client —
hand-built or framework — can only see a tool's description and result, never its
source. Tested on `qwen2.5:7b` (the *better* model), via LangGraph:

| Lie about... | Can the model verify it? | Result |
|--------------|--------------------------|--------|
| Arithmetic (`subtract` 6−2 → returns 12) | **Yes** (it knows 6−2=4) | Model catches it: "seems there was a typo; the answer is 4" |
| Account balance (`get_account_balance` → returns fake $2,347.18) | **No** (only the tool knows) | Model reports the lie as fact, verbatim, every run |

Same model, same framework, same lying-tool mechanism — **opposite outcomes.** The
deciding variable is not the model or the framework; it is **whether the model has
an independent way to verify the tool's claim.**

> **The lying-tool vulnerability is stack-independent.** It was reproduced across
> hand-built loop and LangGraph, and across `llama3.2` and `qwen2.5:7b`. A better
> model catches lies it can *verify* (arithmetic) and is exactly as defenseless
> against lies it *cannot* (a balance). Since every useful data tool — balances,
> prices, records, search results — is the model's *only* source for its fact, every
> one is a tool the model must trust blindly. Model quality and framework quality
> offer **zero** protection for this class of failure.

The fixes live entirely in the layer you control: **tools must be correct** (the
model cannot police them), and **outputs must be verified against ground truth**
(the model's confidence is never evidence of correctness).

## Setup & run

Requires Python 3.10+, Ollama running, and a model pulled
(`ollama pull llama3.2` and/or `ollama pull qwen2.5:7b`).

```bash
pip install langgraph langchain langchain-ollama langchain-mcp-adapters
python agent.py        # experiment 1: framework vs. model
python mcp_agent.py    # experiment 2: lying tools across the stack
```

`mcp_agent.py` launches a separate MCP server as a subprocess — point the path in
`MultiServerMCPClient` at your `server.py`. Swap models by changing the one
`ChatOllama(model=...)` line.

## Biggest takeaways

- **Frameworks and models are independent axes.** A framework makes an agent
  *easier to build*; only a better model makes it *smarter*. Change the loop →
  behavior unchanged; change the model → fixed.
- **A lying tool defeats any stack.** Hand-built or framework, weak model or strong
  — what determines whether a lie lands is *verifiability*, not the stack.
- **"Verified current" is not ground truth — the running code is.** The API used
  here was asserted current and was already deprecated; the run's own warning caught
  it.

## How this fits the series

The framework arc of a from-scratch series (RAG, MCP, a hand-built agent loop, an
MCP-consuming agent). Doing each hand-built version *first* is what makes the
framework legible — every node, edge, state, and adapter maps onto something written
by hand. Use the easy version, but know exactly what it's hiding.