# Session: Zhipu Web Search MCP Integration
Date: 2026-01-16
Duration: ~15 messages

## Context Snapshot
WeeklyAI crawler project - integrated Zhipu Web Search MCP for real-time global AI product discovery with professional prompts following INSTRUCTIONS.md standards.

## What Was Accomplished
- Created `.mcp.json` with Zhipu Web Search MCP configuration
- Added region-based discovery system (US 40%, CN 25%, EU 15%, JP 10%, SEA 10%)
- Implemented professional extraction prompt (Prompt B) with exclusion rules
- Implemented dark horse scoring prompt (Prompt C) with 5-tier system
- Added `web_search_mcp()` function using `glm-4-plus` model
- Updated CLI with `--region`, `--test-search`, `--list-regions` arguments
- Verified GLM connection working

## Key Decisions & Rationale
| Decision | Why | Alternatives Rejected |
|----------|-----|----------------------|
| Use `glm-4-plus` for web search | Only model supporting `web_search` tool | `glm-4.7` doesn't support web_search tool |
| Region-based over source-based | Real-time search vs static RSS feeds | Old source-based approach had stale data |
| Sogou for China, Bing for others | Better coverage per region | Single engine wouldn't work for CN content |

## Current State
- **Working**:
  - `auto_discover.py` with all new features
  - GLM connection verified
  - Region listing and help commands
- **Untested in production**:
  - Actual web search (needs real run with `--region us`)
  - Product extraction pipeline end-to-end
- **Modified files**:
  - `crawler/tools/auto_discover.py` - major update with prompts & region system
  - `.mcp.json` - new file for MCP configuration

## Dead Ends (Don't Retry)
- ❌ Adding `mcpServers` to `.claude/settings.json` — schema doesn't support it, use `.mcp.json` instead

## Next Steps (Prioritized)
1. [ ] Run `python3 tools/auto_discover.py --test-search` to verify web search works
2. [ ] Run `python3 tools/auto_discover.py --region us --dry-run` for US products test
3. [ ] Run full discovery: `python3 tools/auto_discover.py --region all`
4. [ ] Verify products saved to `data/dark_horses/` and `data/rising_stars/`

## Environment & Gotchas
- Use `python3` not `python` on this macOS system
- urllib3 SSL warning can be ignored (LibreSSL 2.8.3 vs OpenSSL)
- API rate limit: 3 seconds between calls (`API_RATE_LIMIT_DELAY`)
- Web search falls back to GLM knowledge if no results

## Key Code/Commands Reference
```bash
# Test commands
python3 tools/auto_discover.py --test           # GLM connection
python3 tools/auto_discover.py --test-search    # Web Search MCP
python3 tools/auto_discover.py --list-regions   # Show region config

# Discovery commands
python3 tools/auto_discover.py --region us      # US only
python3 tools/auto_discover.py --region cn      # China only
python3 tools/auto_discover.py --region all     # All regions
python3 tools/auto_discover.py --region us --dry-run  # Preview mode
```

## Files Changed
| File | Change |
|------|--------|
| `.mcp.json` | NEW - Zhipu Web Search MCP config |
| `crawler/tools/auto_discover.py` | Added REGION_CONFIG, prompts, web_search_mcp(), discover_by_region() |
