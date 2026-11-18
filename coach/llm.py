"""The single boundary between the coach and a language model. Swap the backend here, nowhere else."""
import json
import subprocess

# shortcut: dev backend is the local Claude Code CLI; production replaces this body with the
# Anthropic SDK (Haiku 5.5) or an OpenAI-compatible open-weight host, chosen by the eval.
LEAN = ["--tools", "", "--strict-mcp-config", "--disable-slash-commands",
        "--no-session-persistence", "--setting-sources", ""]


def complete(system, prompt, model="haiku", schema=None):
    """Return (output, cost_usd). output is a dict when schema is given, else text.
    Raises RuntimeError on any failure, so callers never cache or show a broken answer."""
    cmd = ["claude", "-p", "--output-format", "json", "--model", model, "--system-prompt", system, *LEAN]
    if schema:
        cmd += ["--json-schema", json.dumps(schema)]
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=300)
        d = json.loads(r.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:  # OSError: no CLI installed (e.g. in Docker)
        raise RuntimeError(f"LLM call failed: {e}") from e
    out = d.get("structured_output") if schema else d.get("result")
    if d.get("is_error") or not out:
        raise RuntimeError(f"LLM returned no usable output: {str(d.get('result'))[:200]}")
    return out, float(d.get("total_cost_usd") or 0)
