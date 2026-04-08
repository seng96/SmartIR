## Why

目前 `climate` 平台只要 device code 內存在 `commands.on`，每次送出非 `off` 狀態指令前都會先送一次 `on`。這無法清楚表達另一種常見情況：裝置沒有明確的 `on` / `off` 指令，只有單一 `power` toggle 鍵，且只有在需要切換電源狀態時才應送出該指令。

## What Changes

- 為 `climate` 平台新增 `commands.power` 的支援，允許裝置使用單一 toggle 電源碼處理開機與關機流程。
- 保留現有 device code 與 YAML 設定的向後相容性，未啟用新行為的裝置維持既有控制流程。
- 明確定義關機狀態判斷來源，優先使用 `power_sensor`，否則退回 SmartIR 自身已知的 HA 狀態。
- 更新 `custom_components/smartir/climate.py` 的控制流程設計，並補充 `docs/CLIMATE.md` 與必要的 `codes/climate/*.json` 命令型態說明。
- 不改動 `fan`、`media_player`、`light` 平台，也不要求現有所有 device code 立即補齊新 metadata。

## Capabilities

### New Capabilities
- `climate-power-primer`: 讓 `climate` 裝置可使用 `commands.power` 作為單一 toggle 電源命令，並保持 `commands.on` / `commands.off` 的既有相容行為。

### Modified Capabilities

## Impact

- 主要影響 [custom_components/smartir/climate.py](/home/seng96/ha/SmartIR/custom_components/smartir/climate.py) 的送碼邏輯與狀態判斷流程。
- 可能影響 `codes/climate/*.json` 的裝置 metadata 結構，但需保持舊格式仍可正常使用。
- 需要更新 [docs/CLIMATE.md](/home/seng96/ha/SmartIR/docs/CLIMATE.md) 來說明新行為、限制與建議搭配 `power_sensor` 的方式。
- 不涉及外部依賴新增，也不應影響其他控制器傳輸實作或非 `climate` 平台。
