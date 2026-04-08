## Context

SmartIR 的 `climate` 平台目前在送出非 `HVACMode.OFF` 指令時，只要 `commands.on` 存在，就會無條件先送一次 `on`，再送目標模式/風速/溫度的完整狀態碼。這個流程對於有明確開機碼的機型有幫助，但不適合只有 `power` 電源切換鍵的機型；這類裝置需要把 `power` 視為單一 toggle 命令，在開機與關機兩個方向都只於需要切換狀態時才送出。

這個變更主要落在 [custom_components/smartir/climate.py](/home/seng96/ha/SmartIR/custom_components/smartir/climate.py) 的送碼流程與狀態判斷，不需要改動 [custom_components/smartir/controller.py](/home/seng96/ha/SmartIR/custom_components/smartir/controller.py) 的控制器傳輸介面。文件面則需要更新 [docs/CLIMATE.md](/home/seng96/ha/SmartIR/docs/CLIMATE.md)，並為有需求的 `codes/climate/*.json` 明確採用 `power` 型命令格式。

## Goals / Non-Goals

**Goals:**
- 讓 `climate` 裝置可在沒有 `commands.on` / `commands.off` 時，使用 `commands.power` 作為單一 toggle 電源命令。
- 保留現有 device code 與 entity YAML 設定的向後相容性，未啟用新行為的裝置維持既有流程。
- 建立一致的關機狀態判斷順序，優先使用 `power_sensor` 的實體狀態，次選 SmartIR 自身追蹤的 HA 狀態。
- 將新行為收斂到 `commands` 語意本身，避免新增額外 metadata，並明確禁止 `power` 與 `on` / `off` 混用。

**Non-Goals:**
- 不改動 `fan`、`media_player`、`light` 平台。
- 不重新設計 `controller.py` 的傳輸抽象，也不新增控制器類型。
- 不要求現有所有 `codes/climate/*.json` 立即改成 `power`。
- 不嘗試解決所有實體遙控器造成的 HA 狀態不同步問題；本變更只定義在既有狀態來源下的送碼策略。

## Decisions

1. 以 `commands.power` 表達單一 toggle 電源模式，而不是額外 metadata。
   - 決策：`commands.on` / `commands.off` 保留既有語意；若改採 `commands.power`，則 device code 不得同時定義 `on` 或 `off`。`power` 只在需要切換實際電源狀態時送出。
   - 原因：`power` 比 `powerOnBehavior` 更貼近真實遙控器能力，也能避免把 `off` 複製成 `on` 的語意混亂。
   - 替代方案：保留 `powerOnBehavior` metadata。可表達更多變體，但對目前需求來說過度設計，且會讓 code 檔語意變得間接。

2. 關機狀態判斷順序採用 `power_sensor` 優先，否則退回 SmartIR 既有狀態。
   - 決策：若 entity 設定了 `power_sensor`，以 `STATE_OFF` / `STATE_ON` 作為 primer 是否需要送出的第一判斷來源；若未設定，則退回 `self._hvac_mode == HVACMode.OFF` 與 restore state 後的內部狀態作為估計。
   - 原因：`power_sensor` 是目前專案已提供的外部真實狀態來源，最適合用來判斷設備是否真的關機。沒有 sensor 時仍需允許功能工作，因此保留基於 HA 內部狀態的 fallback。
   - 替代方案：沒有 `power_sensor` 就完全不啟用 `commands.power` toggle 模式。這樣最保守，但會讓許多沒有實體電力回報的安裝無法使用此能力。

3. 既有 `commands.on` / `commands.off` 語意預設維持相容，不直接改成條件式送出。
   - 決策：有 `commands.on` 或 `commands.off` 的裝置維持現有行為；只有改採 `commands.power` 的裝置，才採用 toggle 規則。
   - 原因：目前 repository 內已有多個 code 檔帶有 `commands.on`，直接改語意風險過高，可能讓既有使用者行為改變。
   - 替代方案：全域把 `commands.on` 改成只在 off 狀態時送。這最符合直覺，但會造成不易預估的相容性破壞。

4. `power` toggle 模式同時覆蓋開機與關機控制流。
   - 決策：`send_command()` 在目標模式不是 `OFF` 時，若使用 `commands.power` 且目前判定關機，先送 `power` 再送完整狀態碼；在目標模式是 `OFF` 時，若使用 `commands.power` 且目前判定開機，送 `power`，若已判定關機則直接跳過送碼。
   - 原因：這能沿用現有 controller 傳輸抽象與 delay 機制，改動面最小。
   - 替代方案：把 primer 與目標狀態碼組成單一 list 丟給 controller。可行，但會把判斷與組包邏輯耦合在一起，對目前程式結構的可讀性沒有明顯優勢。

## Risks / Trade-offs

- [沒有 `power_sensor` 時可能誤判實際電源狀態] → 以文件明確說明 `commands.power` toggle 模式最佳搭配 `power_sensor`，並允許 fallback 只作為次佳策略。
- [`power` 與 `on` / `off` 若混用會造成語意不清] → 在載入 device code 時明確檢查並拒絕混用格式，文件同步說明互斥規則。
- [部分既有 code 可能其實更適合 `power`] → 預設保持相容，先讓新 capability 可被新增 code 採用，再逐步評估是否需要調整既有 code。
- [HA restore state 與真實設備狀態不一致時，條件判斷仍可能錯誤] → 保持 `power_sensor` 為首選狀態來源，並避免宣稱此功能可完全解決外部遙控器造成的不同步。
