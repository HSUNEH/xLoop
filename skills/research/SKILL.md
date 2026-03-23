---
name: research
description: Multi-source research — ralplan-internal or standalone
level: 2
---

# Research — Multi-Source Investigation

<Purpose>
Investigate specific questions using multiple sources. Primary role: ralplan-internal capability invoked by Planner, Architect, or Critic. Secondary role: standalone command for manual research.
</Purpose>

<Use_When>
- Within ralplan when any agent emits `research_needed`
- User runs `xloop research <topic>` for manual investigation
- During upgrade cycle when improvement approaches need research
</Use_When>

<Sources>
- **Web search**: General web via WebSearch tool (1h cache TTL)
- **ArXiv**: Academic papers via ArXiv API (24h cache TTL)
- **Documentation**: Project docs, library docs via WebFetch (1h cache TTL)
</Sources>

<Error_Boundaries>
Each source adapter wraps calls in try/catch:
- On failure: returns `{ success: false, source: "arxiv", reason: "timeout" }`
- Research proceeds with available sources — never blocks on one failure
- Partial results are valid output
</Error_Boundaries>

<Cache>
- Per-source TTL: ArXiv 24h, web 1h, docs 1h
- Cache key: `hash(query + source + project_root)` — prevents cross-project pollution
- Stored in `.xloop/research/cache/`
- Within ralplan: results shared across loop iterations
</Cache>

<Output>
```json
{
  "question": "the specific question asked",
  "sources": [{"url": "...", "type": "web|arxiv|docs"}],
  "findings": [{"text": "...", "confidence": "high|medium|low"}],
  "cached": false,
  "timestamp": "2026-03-24T..."
}
```
- Ralplan-internal: results passed directly to requesting agent as structured context
- Standalone: saved to `.xloop/research/{topic}-{timestamp}.json`
</Output>

<PAL_Router>
- Haiku: keyword extraction, simple lookups
- Sonnet: synthesis, analysis, comparison
- Opus: deep research requiring multi-step reasoning
</PAL_Router>
