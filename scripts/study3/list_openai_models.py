"""$0 model-list check for natural configuration N4 (STUDY3.md §B′1): which older/smaller OpenAI chat models are on the
Hexa Agents key. Prints model ids only (never keys). Run via scripts/with_keys.sh.
"""

import os

from openai import OpenAI

ids = sorted(m.id for m in OpenAI(api_key=os.environ["OPENAI_API_KEY"]).models.list().data)
print(len(ids), "models")
for i in ids:
    if any(s in i for s in ("gpt-3.5", "gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o", "gpt-4.1", "gpt-5-mini", "gpt-5-nano")):
        print(i)
