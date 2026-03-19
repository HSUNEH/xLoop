---
description: "Add YouTube/web URLs to a NotebookLM notebook"
argument-hint: "<notebook_title> <url1> [url2 ...]"
allowed-tools:
  - Bash
---

Add the provided URLs as sources to a new NotebookLM notebook.

Execute this command:

```
python xLoop/scripts/notebooklm_add.py $ARGUMENTS
```

Present the output directly to the user. If the script reports an error:
- "Not authenticated" → guide the user to run `notebooklm login`
- "notebooklm-py not installed" → guide the user to run `pip install notebooklm-py[browser]`
- Other errors → explain and suggest fixes
