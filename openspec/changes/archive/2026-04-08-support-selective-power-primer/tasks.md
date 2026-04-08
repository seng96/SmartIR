## 1. Climate 送碼策略實作

- [x] 1.1 在 `custom_components/smartir/climate.py` 支援 `commands.power` 作為單一 toggle 電源命令，並保留既有 `commands.on` / `commands.off` 行為。
- [x] 1.2 在 `custom_components/smartir/climate.py` 實作「是否需要 power primer」的判斷流程，優先使用 `power_sensor`，否則退回 HA 內部狀態。
- [x] 1.3 調整 `custom_components/smartir/climate.py` 的 `send_command()`，讓 `commands.power` 型裝置在需要切換電源狀態時才送出 `power`，且在已判定關機時收到 `OFF` 會跳過送碼。

## 2. Device Code 與相容性調整

- [x] 2.1 定義 `codes/climate/*.json` 使用 `commands.power` 的格式，並明確規定不得與 `commands.on` / `commands.off` 混用。
- [x] 2.2 至少更新一個需要條件式 power primer 的 `codes/climate/*.json` 範例，作為新行為的參考實作。

## 3. 文件更新

- [x] 3.1 更新 `docs/CLIMATE.md`，說明 `commands.power` 的 toggle 行為、適用情境與 `power_sensor` 的建議搭配。
- [x] 3.2 在文件中補充互斥規則與相容性說明，明確標示 `commands.power` 不得與 `commands.on` / `commands.off` 混用。

## 4. 驗證

- [x] 4.1 驗證 `climate` 在僅提供 `commands.power` 且判定關機時，會依序送出 `commands.power`、等待 `delay`、再送目標狀態碼。
- [x] 4.2 驗證 `climate` 在僅提供 `commands.power` 且判定開機時，會直接送出目標狀態碼，不額外送 `commands.power`。
- [x] 4.3 驗證 `climate` 在僅提供 `commands.power` 且判定已關機時收到 `HVACMode.OFF`，會跳過送碼。
- [x] 4.4 驗證既有 `commands.on` / `commands.off` 行為不受影響，且混用 `commands.power` 與 `commands.on` / `commands.off` 會被拒絕。
