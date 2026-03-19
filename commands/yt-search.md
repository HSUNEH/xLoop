---
description: "Search YouTube and return structured video results"
argument-hint: "<query> [--count N] [--months N] [--no-date-filter] [--min-views N] [--min-duration M] [--max-duration M] [--channel NAME] [--exclude-channel NAME]"
allowed-tools:
  - Bash
---

Run the YouTube search script with the user's arguments and present the results.

Execute this command:

```
python xLoop/scripts/yt_search.py $ARGUMENTS
```

Present the output directly to the user. If the script reports an error, explain it and suggest fixes.
