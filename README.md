# shioaji-mcp

永豐金證券 [Shioaji](https://sinotrade.github.io/) API 的唯讀 [MCP](https://modelcontextprotocol.io/) 伺服器。讓 Claude Code 等 MCP client 查詢行情與帳務資料。**不提供任何下單工具**，無法下單、改單或刪單。

## 需求

- Python 3.12 以上
- [uv](https://docs.astral.sh/uv/)
- 永豐金證券帳戶，並已在 API 管理頁面申請 API Key

## 安裝

```bash
git clone https://github.com/xianyuntang/shioaji-mcp.git
cd shioaji-mcp
uv sync
```

在專案根目錄建立 `.env`（已列入 `.gitignore`）：

```dotenv
SJ_API_KEY=你的_api_key
SJ_SEC_KEY=你的_secret_key
SJ_PRODUCTION=false
# 選填，只有 ca_status 會用到
SJ_CA_PATH=/絕對路徑/Sinopac.pfx
SJ_CA_PASSWD=憑證密碼
```

加入 Claude Code：

```bash
claude mcp add shioaji -- uv --directory /path/to/shioaji-mcp run --env-file .env main.py
```

其他 MCP client（JSON 設定）：

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

## 環境變數

| 變數 | 必填 | 預設 | 說明 |
|---|---|---|---|
| `SJ_API_KEY` | 是 | — | 永豐 API 管理頁面取得的 API Key |
| `SJ_SEC_KEY` | 是 | — | 與 `SJ_API_KEY` 配對的 Secret Key |
| `SJ_PRODUCTION` | 否 | `false` | 設 `true` 登入正式帳戶，否則使用模擬環境 |
| `SJ_CA_PATH` | 否 | — | 憑證檔（`.pfx`）的絕對路徑 |
| `SJ_CA_PASSWD` | 否 | — | 憑證密碼（通常是身分證字號） |

憑證只用來讓 `ca_status` 回報到期時間。查詢功能不需要憑證，憑證啟用失敗也不影響查詢。

第一次呼叫工具時才登入，之後整個程序共用同一個 session。

## 工具

**商品與行情**

| 工具 | 說明 |
|---|---|
| `get_contract` | 商品資料（參考價、漲跌停、當沖、資券資訊） |
| `get_snapshots` | 最新快照，一次最多 500 檔 |
| `get_kbars` | 指定日期區間的 1 分 K |
| `get_ticks` | 單日逐筆成交（全部、最後 N 筆或時間區間） |
| `scan` | 排行：漲跌幅、漲跌價、振幅、成交量、成交金額、成交筆數 |
| `credit_enquires` | 資券餘額 |
| `short_stock_sources` | 借券賣出餘額 |
| `disposition_stocks` | 處置股 |
| `attention_stocks` | 注意股 |
| `usage` | API 連線數與每日流量額度 |

**帳務**

| 工具 | 說明 |
|---|---|
| `list_accounts` | 證券／期貨帳戶 |
| `account_balance` | 交割銀行帳戶餘額 |
| `settlements` | 交割款（T、T+1、T+2） |
| `trading_limits` | 證券交易額度、融資融券額度 |
| `futures_margin` | 期權權益數、保證金、風險指標 |
| `list_positions` / `list_position_detail` | 未實現損益與持倉明細 |
| `list_profit_loss` / `list_profit_loss_detail` / `list_profit_loss_summary` | 已實現損益 |
| `list_trades` | 今日委託與成交 |
| `ca_status` | 憑證啟用結果與到期時間 |

商品代碼格式：股票 `2330`、期貨近月連續 `TXFR1`、選擇權 `TXO31200G6`、指數 `IX0001`（加權指數）。

行情查詢會計入 Shioaji 每日流量額度，不要用來輪詢即時報價。

## 免責聲明

非官方專案，與永豐金證券無關。依現狀提供，不負任何擔保，使用風險自負。

## 授權

[MIT](LICENSE)
