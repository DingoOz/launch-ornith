# launch-ornith

Launch [Claude Code](https://claude.com/claude-code) wired to a local **Ornith**
model served by [Ollama](https://ollama.com), with an fp16 KV cache and a large
context window.

## What it does

`launch-ornith.sh`:

1. Interactively prompts for a context window (32K/64K/128K/256K) and KV cache
   precision (fp16 / q8_0 / Q4_0).
2. Checks the GPU is healthy, restarts the Ollama server with the chosen
   settings, and preloads the model.
3. **Verifies the model is fully on the GPU** — if the KV cache spills to CPU it
   aborts and tells you to pick a smaller context / more compressed cache.
4. Hands off to Claude Code, appending the editing rules in
   `ornith-editing-rules.md` to the system prompt.

Verified on an RTX 5060 Ti (16 GB): 256K fp16 fits, 100% on GPU.

## The editing rules

Local models often fail Claude Code's `Edit` tool because `old_string` must
match the file byte-for-byte. `ornith-editing-rules.md` is appended to the
system prompt (via `ollama launch claude -- --append-system-prompt ...`) to
steer the model toward small, verbatim, copy-don't-reconstruct edits.

## Usage

```bash
./launch-ornith.sh
```

## Requirements

- `ollama` (with `ollama launch claude` integration support)
- `nvidia-smi` / an NVIDIA GPU
- Claude Code
