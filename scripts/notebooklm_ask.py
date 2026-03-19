#!/usr/bin/env python3
"""Ask a question to a NotebookLM notebook and get an AI answer."""

import asyncio
import json
import sys


def parse_args(argv: list[str]) -> dict:
    """Parse notebook_id, question, --conversation-id, --json from argv.

    Usage:
        notebooklm_ask.py <notebook_id> "<question>"
        notebooklm_ask.py <notebook_id> "<question>" --conversation-id <id>
        notebooklm_ask.py <notebook_id> "<question>" --json
    """
    args = argv[1:]
    conversation_id = None
    json_output = False
    positional = []
    i = 0

    while i < len(args):
        if args[i] == "--conversation-id" and i + 1 < len(args):
            conversation_id = args[i + 1]
            i += 2
        elif args[i] == "--json":
            json_output = True
            i += 1
        else:
            positional.append(args[i])
            i += 1

    if len(positional) < 2:
        print(
            "Usage: notebooklm_ask.py <notebook_id> \"<question>\" "
            "[--conversation-id ID] [--json]",
            file=sys.stderr,
        )
        sys.exit(1)

    notebook_id = positional[0]
    question = " ".join(positional[1:])

    return {
        "notebook_id": notebook_id,
        "question": question,
        "conversation_id": conversation_id,
        "json_output": json_output,
    }


async def ask_notebook(
    notebook_id: str,
    question: str,
    conversation_id: str | None = None,
) -> dict:
    """Ask a question to a NotebookLM notebook.

    Returns:
        Dict with answer, conversation_id, turn_number, references.
    """
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        print(
            "Error: notebooklm-py not installed. "
            "Run: pip install notebooklm-py[browser]",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        async with (await NotebookLMClient.from_storage()) as client:
            result = await client.chat.ask(
                notebook_id=notebook_id,
                question=question,
                conversation_id=conversation_id,
            )
            references = []
            for ref in result.references:
                entry = {"citation_number": ref.citation_number}
                if ref.cited_text:
                    entry["cited_text"] = ref.cited_text
                if ref.source_id:
                    entry["source_id"] = ref.source_id
                references.append(entry)

            return {
                "answer": result.answer,
                "conversation_id": result.conversation_id,
                "turn_number": result.turn_number,
                "references": references,
            }
    except FileNotFoundError:
        print(
            "Error: Not authenticated. Run 'notebooklm login' first.",
            file=sys.stderr,
        )
        sys.exit(1)
    except TimeoutError:
        print(
            "Error: Request timed out. Check your network and try again.",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "404" in error_msg:
            print(
                f"Error: Notebook '{notebook_id}' not found. "
                "Check the notebook ID and try again.",
                file=sys.stderr,
            )
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def print_text_result(data: dict) -> None:
    """Print answer in human-readable text format."""
    print(data["answer"])

    if data["references"]:
        print(f"\n{'─' * 40}")
        print(f"References ({len(data['references'])})")
        for ref in data["references"]:
            num = ref.get("citation_number", "?")
            text = ref.get("cited_text", "")
            if text:
                preview = text[:120] + "..." if len(text) > 120 else text
                print(f"  [{num}] {preview}")
            else:
                print(f"  [{num}] (source: {ref.get('source_id', 'unknown')})")

    print(f"\nConversation ID: {data['conversation_id']}", file=sys.stderr)


def print_json_result(data: dict) -> None:
    """Print answer as JSON to stdout."""
    print(json.dumps(data, ensure_ascii=False))


def main() -> None:
    parsed = parse_args(sys.argv)
    data = asyncio.run(
        ask_notebook(
            notebook_id=parsed["notebook_id"],
            question=parsed["question"],
            conversation_id=parsed["conversation_id"],
        )
    )
    if parsed["json_output"]:
        print_json_result(data)
    else:
        print_text_result(data)


if __name__ == "__main__":
    main()
