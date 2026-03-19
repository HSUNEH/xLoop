---
description: "Search Reddit and Hacker News for community discussions"
argument-hint: "<reddit|hn|all> <query> [--count N] [--subreddit NAME] [--min-score N] [--time d|w|m|y]"
allowed-tools:
  - Bash
---

Run the community search script with the user's arguments and present the results.

Execute this command:

```
python xLoop/scripts/community_search.py $ARGUMENTS
```

Present the output directly to the user. If the script reports an error, explain it and suggest fixes.
