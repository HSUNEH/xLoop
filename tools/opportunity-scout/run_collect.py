#!/usr/bin/env python3
"""CLI wrapper for opportunity-scout data collection."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import collect_all


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_collect.py <query> [domain]")
        print("  domain: tech, saas, dev_tools, content, auto (default: auto)")
        sys.exit(1)

    query = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else "auto"

    print(f"\n{'='*60}")
    print(f"  Opportunity Scout - Data Collection")
    print(f"  Query: {query}")
    print(f"  Domain: {domain}")
    print(f"{'='*60}\n")

    results = collect_all(query, domain)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "latest_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n[Done] Results saved to {output_path}")
    print(json.dumps(results, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
