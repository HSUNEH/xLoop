---
description: "Search arXiv papers and return structured results"
argument-hint: "<query> [--count N] [--sort relevance|date]"
allowed-tools:
  - Bash
---

Run the arXiv search script with the user's arguments and present the results.

Execute this command:

```
python xLoop/scripts/arxiv_search.py $ARGUMENTS
```

Present the output directly to the user. If the script reports an error, explain it and suggest fixes.
