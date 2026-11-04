# shioaji-mcp

MCP server for [Shioaji](https://sinotrade.github.io/) (Sinopac securities API): contracts, snapshots, K bars, ticks, scanners, margin/short balances, disposition/attention stocks, positions, PnL, settlements, today's trades. Read-only — no order tools.

## Setup

```bash
uv sync
```

Add to Claude Code:

```bash
# put keys in .env (gitignored), then:
claude mcp add shioaji -- uv --directory /Volumes/Data/self/repos/shioaji-mcp run --env-file .env main.py
```

## Env

| Var | Default | Note |
|---|---|---|
| `SJ_API_KEY` / `SJ_SEC_KEY` | required | From Sinopac API management |
| `SJ_PRODUCTION` | `false` | Set `true` for the real account (default is simulation) |

Login happens lazily on the first tool call.
