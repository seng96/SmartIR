## ADDED Requirements

### Requirement: SmartIR MUST support explicit fast reload of its YAML platforms
SmartIR MUST 提供一條明確的重新載入路徑，讓使用者在不重啟整個 Home Assistant 的情況下，重新載入 SmartIR 所管理的 YAML platform entities。

#### Scenario: Reload 會重建 SmartIR 平台 entity
- **WHEN** 使用者觸發 SmartIR 的 reload 流程
- **THEN** SmartIR MUST 重設並重新建立 `climate`、`fan`、`light`、`media_player` 平台中由 SmartIR 載入的 entities

#### Scenario: Reload 不要求完整 Home Assistant 重啟
- **WHEN** SmartIR reload 流程成功完成
- **THEN** 使用者 MUST 不需要完整重啟 Home Assistant 即可讓 SmartIR 的 YAML platform 變更生效

### Requirement: Reload MUST read the latest YAML configuration
SmartIR reload 流程 MUST 重新讀取目前最新的 YAML 設定，而不是沿用啟動時的舊設定快照。

#### Scenario: 更新 YAML 後 reload 會套用最新 platform 設定
- **WHEN** 使用者修改 `configuration.yaml` 中 SmartIR 相關的 platform 設定，然後觸發 SmartIR reload
- **THEN** SmartIR MUST 依據最新 YAML 內容重新建立 entities 與其設定

#### Scenario: 移除 YAML 配置後 reload 會移除對應 entity
- **WHEN** 使用者從 YAML 中移除某個 SmartIR platform entity 設定，然後觸發 SmartIR reload
- **THEN** SmartIR MUST 移除該設定原本建立的 entity，且不得殘留舊 entity

### Requirement: Reload MUST re-read device JSON definitions from disk
SmartIR reload 流程 MUST 重新從磁碟讀取 device code JSON 檔，讓 `codes` 目錄中的變更能在 reload 後生效。

#### Scenario: 更新現有 device JSON 後 reload 會讀入新內容
- **WHEN** 使用者修改 `codes/climate/*.json`、`codes/fan/*.json`、`codes/light/*.json` 或 `codes/media_player/*.json` 中既有裝置定義，然後觸發 SmartIR reload
- **THEN** SmartIR MUST 在 reload 過程中重新讀取更新後的 JSON 檔案內容

#### Scenario: 裝置定義變更後 entity 使用新命令集
- **WHEN** 某個 SmartIR entity 對應的 device JSON 命令、metadata 或支援能力已更新，且使用者觸發 reload
- **THEN** 該 entity MUST 依更新後的裝置定義重新初始化

### Requirement: Reload MUST clean up entity listeners and callbacks safely
SmartIR reload 流程 MUST 在重設 entities 時正確解除既有事件監聽與 callback，避免 reload 後產生殘留狀態或重複處理。

#### Scenario: Reload 後不得殘留舊的 sensor state listener
- **WHEN** SmartIR entity 在一般運作期間建立了 `temperature_sensor`、`humidity_sensor`、`power_sensor` 等事件監聽，且使用者觸發 reload
- **THEN** 舊 entity 的監聽 MUST 在 entity 被移除時正確解除註冊

#### Scenario: 多次 reload 也不應累積重複 callback
- **WHEN** 使用者連續多次觸發 SmartIR reload
- **THEN** SmartIR MUST 不得因重複註冊 listener 或 callback 而造成同一事件被處理多次

### Requirement: Documentation MUST describe reload scope and limitations
SmartIR 文件 MUST 清楚說明快速 reload 的適用範圍與限制，避免使用者誤以為所有 Home Assistant 設定都能藉由此流程即時生效。

#### Scenario: 文件說明可透過 reload 生效的變更類型
- **WHEN** 使用者閱讀 SmartIR 文件中的 reload 說明
- **THEN** 文件 MUST 明確指出 SmartIR 的 YAML platform 設定與 `codes` 目錄 device JSON 變更可透過 reload 生效

#### Scenario: 文件說明仍需完整重啟的情況
- **WHEN** 使用者閱讀 SmartIR 文件中的 reload 說明
- **THEN** 文件 MUST 明確指出超出 SmartIR 管轄範圍或 Home Assistant 核心限制的設定變更，仍可能需要完整重啟
