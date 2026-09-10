"""Global test isolation.

The normal suite must remain deterministic even when a developer has a local
.env configured for live Gemini experiments. Live provider coverage lives under
tests/live and must be selected explicitly.
"""

import os

os.environ["LLM_PROVIDER"] = "heuristic"
