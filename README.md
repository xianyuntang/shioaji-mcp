# shioaji-mcp

Read-only [MCP](https://modelcontextprotocol.io/) server for [Shioaji](https://sinotrade.github.io/), the Sinopac (永豐金證券) trading API. It exposes market data and account queries to MCP clients such as Claude Code. It has **no order tools**: it cannot place, modify or cancel orders.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A Sinopac securities account with API keys (apply in Sinopac's API management page)

## Setup

```bash
git clone https://github.com/xianyuntang/shioaji-mcp.git
cd shioaji-mcp
uv sync
```

Create `.env` in the project root (it is gitignored):

```dotenv
SJ_API_KEY=your_api_key
SJ_SEC_KEY=your_secret_key
SJ_PRODUCTION=false
# Optional, only needed for ca_status
SJ_CA_PATH=/absolute/path/to/Sinopac.pfx
SJ_CA_PASSWD=your_ca_password
```

Add it to Claude Code:

```bash
claude mcp add shioaji -- uv --directory /path/to/shioaji-mcp run --env-file .env main.py
```

Other MCP clients (JSON config):

```json
{
  "mcpServers": {
    "shioaji": {
      "command": "uv",
      "args": ["--directory", "/path/to/shioaji-mcp", "run", "--env-file", ".env", "main.py"]
    }
  }
}
```

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SJ_API_KEY` | yes | — | API key from Sinopac API management |
| `SJ_SEC_KEY` | yes | — | Secret key paired with `SJ_API_KEY` |
| `SJ_PRODUCTION` | no | `false` | `true` logs in to the real account; otherwise the simulation environment is used |
| `SJ_CA_PATH` | no | — | Absolute path to the certificate file (`.pfx`) |
| `SJ_CA_PASSWD` | no | — | Certificate password (usually your national ID) |

The certificate is only activated so `ca_status` can report its expiry. Queries do not need it, and a failed activation does not block them.

Login happens lazily on the first tool call, and the session is reused for the life of the process.

## Tools

**Contracts and market data**

| Tool | Description |
|---|---|
| `get_contract` | Contract details (reference price, limit up/down, day-trade, margin/short info) |
| `get_snapshots` | Latest snapshot for up to 500 codes |
| `get_kbars` | 1-minute K bars for a date range |
| `get_ticks` | Ticks of one day (all, last N, or a time range) |
| `scan` | Rankings: change %, change price, day range, volume, amount, tick count |
| `credit_enquires` | Margin purchase / short sale balances (資券餘額) |
| `short_stock_sources` | Shares available for short selling (借券賣出餘額) |
| `disposition_stocks` | Disposition stocks (處置股) |
| `attention_stocks` | Attention stocks (注意股) |
| `usage` | API connections and daily traffic quota |

**Account**

| Tool | Description |
|---|---|
| `list_accounts` | Stock / futures accounts |
| `account_balance` | Settlement bank account balance |
| `settlements` | Upcoming settlements (T, T+1, T+2) |
| `trading_limits` | Stock trading, margin and short limits |
| `futures_margin` | Futures/options equity, margin, risk indicator |
| `list_positions` / `list_position_detail` | Open positions with unrealized PnL |
| `list_profit_loss` / `list_profit_loss_detail` / `list_profit_loss_summary` | Realized PnL |
| `list_trades` | Today's orders and fills |
| `ca_status` | Certificate activation result and expiry |

Code formats: stock `2330`, continuous futures `TXFR1`, option `TXO31200G6`, index `IX0001` (TAIEX).

Market data calls count toward Shioaji's daily traffic quota. Do not poll them for live prices.

## Disclaimer

Unofficial project, not affiliated with Sinopac. Provided as-is with no warranty. Use at your own risk.

## License

[MIT](LICENSE)
