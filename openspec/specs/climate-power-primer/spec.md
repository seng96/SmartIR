## Purpose

定義 SmartIR `climate` 裝置在 `commands.on` / `commands.off` 與 `commands.power` 兩種互斥電源命令型態下的送碼行為。

## Requirements

### Requirement: Climate 裝置命令型態必須明確且互斥
`climate` device code SHALL 支援兩種互斥的電源命令型態：既有的 `commands.on` / `commands.off` 型態，或新的 `commands.power` toggle 型態。

#### Scenario: 未提供 power 指令的既有 device code 維持相容
- **WHEN** `codes/climate/*.json` 仍使用既有格式且未提供 `commands.power`
- **THEN** SmartIR MUST 維持目前既有的送碼行為，不因這次變更改變既有 `commands.on` 的處理方式

#### Scenario: device code 提供 power 指令
- **WHEN** `codes/climate/*.json` 提供 `commands.power`
- **THEN** SmartIR MUST 將 `commands.power` 視為單一 toggle 電源命令

#### Scenario: power 與 on/off 不可混用
- **WHEN** `codes/climate/*.json` 同時提供 `commands.power` 與 `commands.on` 或 `commands.off`
- **THEN** SmartIR MUST 將其視為無效命令配置並拒絕載入該裝置

### Requirement: power 指令只在需要切換電源狀態時送出
當 `climate` 裝置提供 `commands.power` 時，SmartIR MUST 只在需要切換設備電源狀態時送出一次 `commands.power`。

#### Scenario: 目前判定為關機時先送 power 再送狀態碼
- **WHEN** entity 目標模式不是 `HVACMode.OFF`，device code 提供 `commands.power`，且 SmartIR 判定設備目前為關機
- **THEN** SmartIR MUST 依序送出 `commands.power`、等待既有 `delay`、再送出目標狀態對應的 IR 指令

#### Scenario: 目前判定為開機時直接送狀態碼
- **WHEN** entity 目標模式不是 `HVACMode.OFF`，device code 提供 `commands.power`，且 SmartIR 判定設備目前不是關機
- **THEN** SmartIR MUST 跳過 `commands.power` primer，直接送出目標狀態對應的 IR 指令

#### Scenario: 目標模式為關機且目前為開機時送出 power
- **WHEN** entity 目標模式為 `HVACMode.OFF`，device code 提供 `commands.power`，且 SmartIR 判定設備目前為開機
- **THEN** SmartIR MUST 送出一次 `commands.power`

#### Scenario: 目標模式為關機且目前已為關機時跳過送碼
- **WHEN** entity 目標模式為 `HVACMode.OFF`，device code 提供 `commands.power`，且 SmartIR 判定設備目前已經是關機
- **THEN** SmartIR MUST 跳過送碼，避免 toggle 指令誤將設備開啟

### Requirement: power primer 的狀態判斷必須有明確優先順序
當 SmartIR 需要判斷 `climate` 設備目前是否為關機以決定是否送出 primer 時，系統 MUST 優先使用 `power_sensor` 的實際狀態；若未設定 `power_sensor`，則 MUST 使用 SmartIR 已知的 HA 實體狀態作為 fallback。

#### Scenario: 有 power_sensor 時優先使用實際狀態
- **WHEN** entity 已設定 `power_sensor`，且其狀態可判定為 `on` 或 `off`
- **THEN** SmartIR MUST 以該 `power_sensor` 狀態作為是否插入 primer 的判斷依據

#### Scenario: 沒有 power_sensor 時使用 HA 內部狀態 fallback
- **WHEN** entity 未設定 `power_sensor`
- **THEN** SmartIR MUST 使用 restore state 與當前 `hvac_mode` 所反映的內部狀態作為是否插入 primer 的 fallback 判斷依據

#### Scenario: 文件需說明最佳使用條件
- **WHEN** `climate` 平台文件描述 `commands.power` toggle 功能
- **THEN** 文件 MUST 明確說明 `commands.power` 不得與 `commands.on` / `commands.off` 混用，且搭配 `power_sensor` 可提供較可靠的狀態判斷
