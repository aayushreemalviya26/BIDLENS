import subprocess
import sys


def run_stage(stage, work, env):
    """Preserve diagnostics locally, but never return paths/secrets to clients."""
    try:
        result = subprocess.run([sys.executable, stage], cwd=work, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"Processing stage {stage} timed out. Retry processing.") from error
    if result.returncode:
        # ProviderError messages are authored by our adapter and contain no key.
        marker = "ProviderError: "
        if marker in result.stderr:
            message = result.stderr.rsplit(marker, 1)[-1].splitlines()[0]
            raise RuntimeError(message)
        if stage in {"embed.py", "embed_chunk.py", "embed_queries.py", "retrieve.py"}:
            raise RuntimeError(f"Embedding stage {stage} failed. Ensure all-MiniLM-L6-v2 is cached and enough memory is available.")
        raise RuntimeError(f"Processing stage {stage} failed (exit {result.returncode}). Review the local pipeline configuration.")
    print(f"Completed processing stage: {stage}", flush=True)
