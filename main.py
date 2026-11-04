"""Shioaji (Sinopac) MCP server. Read-only: market data and account queries, no order placement.

Env (same names as the official `shioaji server`):
  SJ_API_KEY, SJ_SEC_KEY   required
  SJ_PRODUCTION            "true" for the real account; default false = simulation
  SJ_CA_PATH, SJ_CA_PASSWD optional; activated for ca_status only (no orders here)

Follows the 1.7 API (`api.contracts.get/info`, exchange index codes like IX0001).
Docs: https://sinotrade.github.io/llms-full.txt
"""

import functools
import json
import os
from typing import Literal

import shioaji as sj
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

mcp = MCPServer("shioaji")
PRODUCTION = os.environ.get("SJ_PRODUCTION", "false").lower() == "true"
Account = Literal["stock", "futures"]


def tool(fn):
    """mcp.tool() that passes Shioaji's error text to the client (MCPServer hides unexpected errors)."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (sj.ShioajiError, ValueError, KeyError) as e:
            raise ToolError(f"{type(e).__name__}: {e}") from e
    return mcp.tool()(wrapper)

_api: sj.Shioaji | None = None
_trades_synced = False


def api() -> sj.Shioaji:
    # One logged-in session per process; docs ask not to call login() repeatedly.
    global _api
    if _api is None:
        a = sj.Shioaji(simulation=not PRODUCTION)
        a.login(api_key=os.environ["SJ_API_KEY"], secret_key=os.environ["SJ_SEC_KEY"])
        _api = a
        # CA is only for orders; this server never places any, so a bad CA must not block queries.
        global _ca_error
        if (path := os.environ.get("SJ_CA_PATH")) and (pw := os.environ.get("SJ_CA_PASSWD")):
            try:
                a.activate_ca(ca_path=path, ca_passwd=pw)
            except Exception as e:
                _ca_error = str(e)
    return _api


_ca_error: str | None = None


@tool
def ca_status() -> dict:
    """Certificate (SJ_CA_PATH) activation result and expiry time."""
    a = api()
    if not os.environ.get("SJ_CA_PASSWD"):
        return {"activated": False, "reason": "SJ_CA_PATH / SJ_CA_PASSWD not set"}
    if _ca_error:
        return {"activated": False, "error": _ca_error}
    return {"activated": True, "expire_time": str(a.get_ca_expiretime(a.stock_account.person_id))}


def out(obj):
    """Shioaji objects expose .dict(); make everything JSON-safe."""
    if isinstance(obj, list):
        return [out(o) for o in obj]
    return json.loads(json.dumps(obj.dict() if hasattr(obj, "dict") else obj, default=str))


def contract(code: str):
    c = api().contracts.get(code)
    if c is None:
        raise ValueError(f"contract not found: {code}")
    return c


def account(kind: Account):
    a = api()
    return a.stock_account if kind == "stock" else a.futopt_account


# ---------- contracts ----------

@tool
def get_contract(code: str) -> dict:
    """Contract details: name, reference, limit up/down, unit, day-trade, margin/short info...
    code: stock '2330', continuous futures 'TXFR1'/'TXFR2', option 'TXO31200G6', index 'IX0001' (TAIEX)."""
    return out(api().contracts.info(contract(code)))


# ---------- market data ----------
# Docs: these count toward the daily traffic quota; don't poll them for live prices.

@tool
def get_snapshots(codes: list[str]) -> list:
    """Latest snapshot (open/high/low/close, change, volume, best bid/ask) for up to 500 codes."""
    return out(api().snapshots([contract(c) for c in codes]))


@tool
def get_kbars(code: str, start: str, end: str) -> dict:
    """1-minute K bars, dates YYYY-MM-DD. ts is nanoseconds since epoch.
    History from 2020-03-02 (stocks/index), 2020-03-22 (futures). Use TXFR1 for expired futures."""
    return out(api().kbars(contract(code), start=start, end=end))


@tool
def get_ticks(
    code: str,
    date: str,
    last_count: int | None = None,
    time_start: str | None = None,
    time_end: str | None = None,
) -> dict:
    """Ticks of one trading day (YYYY-MM-DD). Give last_count for the last N ticks,
    or time_start/time_end ('HH:MM:SS') for a range; otherwise the whole day."""
    if last_count:
        return out(api().ticks(contract(code), date=date,
                               query_type=sj.TicksQueryType.LastCount, last_cnt=last_count))
    if time_start or time_end:
        return out(api().ticks(contract(code), date=date, query_type=sj.TicksQueryType.RangeTime,
                               time_start=time_start or "00:00:00", time_end=time_end or "23:59:59"))
    return out(api().ticks(contract(code), date=date))


@tool
def scan(
    scanner_type: Literal["ChangePercentRank", "ChangePriceRank", "DayRangeRank",
                          "VolumeRank", "AmountRank", "TickCountRank"],
    count: int = 20,
    ascending: bool = False,
    date: str | None = None,
) -> list:
    """Stock ranking (top gainers, volume, amount...). ascending=False gives the top; date YYYY-MM-DD, default today."""
    return out(api().scanners(scanner_type=getattr(sj.ScannerType, scanner_type),
                              count=count, ascending=ascending, date=date))


@tool
def credit_enquires(codes: list[str]) -> list:
    """Margin purchase / short sale balances (資券餘額) for stocks."""
    return out(api().credit_enquires([contract(c) for c in codes]))


@tool
def short_stock_sources(codes: list[str]) -> list:
    """Shares available for short selling (借券賣出餘額) for stocks."""
    return out(api().short_stock_sources([contract(c) for c in codes]))


@tool
def disposition_stocks() -> dict:
    """Disposition stocks (處置股) currently under trading restrictions."""
    return out(api().punish())


@tool
def attention_stocks() -> dict:
    """Attention stocks (注意股) announced by the exchange."""
    return out(api().notice())


@tool
def usage() -> dict:
    """API connections and daily traffic used/limit/remaining (bytes). Quota resets 08:00 on trading days."""
    u = api().usage()
    return {k: getattr(u, k) for k in ("connections", "bytes", "limit_bytes", "remaining_bytes")}


# ---------- account ----------

@tool
def list_accounts() -> list:
    """Stock / futures accounts available after login."""
    return out(api().list_accounts())


@tool
def account_balance() -> dict:
    """Settlement bank account balance (Sinopac bank, sub-account, LINE Bank only)."""
    return out(api().account_balance())


@tool
def settlements() -> list:
    """Upcoming stock settlement amounts (T, T+1, T+2)."""
    return out(api().settlements())


@tool
def trading_limits() -> dict:
    """Stock account trading, margin and short limits."""
    return out(api().trading_limits())


@tool
def futures_margin() -> dict:
    """Futures/options account equity, margin, risk indicator."""
    return out(api().margin())


@tool
def list_positions(account_type: Account = "stock", unit: Literal["Common", "Share"] = "Common") -> list:
    """Open positions with unrealized PnL. unit applies to stocks: Common = lots, Share = shares.
    Each row's id can be passed to list_position_detail."""
    return out(api().list_positions(account(account_type), unit=getattr(sj.Unit, unit)))


@tool
def list_position_detail(detail_id: int, account_type: Account = "stock") -> list:
    """Per-lot breakdown of one position (detail_id = position id from list_positions)."""
    return out(api().list_position_detail(account(account_type), detail_id=detail_id))


@tool
def list_profit_loss(begin_date: str, end_date: str, account_type: Account = "stock") -> list:
    """Realized PnL records between dates (YYYY-MM-DD). Each row's id works with list_profit_loss_detail."""
    return out(api().list_profit_loss(account(account_type), begin_date=begin_date, end_date=end_date))


@tool
def list_profit_loss_detail(detail_id: int, account_type: Account = "stock") -> list:
    """Breakdown of one realized PnL record (detail_id = id from list_profit_loss)."""
    return out(api().list_profit_loss_detail(account(account_type), detail_id=detail_id))


@tool
def list_profit_loss_summary(begin_date: str, end_date: str, account_type: Account = "stock") -> dict:
    """Realized PnL summarized per instrument plus totals, dates YYYY-MM-DD."""
    return out(api().list_profit_loss_summary(account(account_type), begin_date=begin_date, end_date=end_date))


@tool
def list_trades() -> list:
    """Today's orders and fills across all accounts."""
    # Docs: list is empty after login until one update_status; afterwards trades update from push events.
    global _trades_synced
    a = api()
    if not _trades_synced:
        a.update_status()
        _trades_synced = True
    return out(a.list_trades())


if __name__ == "__main__":
    mcp.run()
