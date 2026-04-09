## Why

目前 SmartIR 採用 YAML platform 模式，修改 `configuration.yaml` 中的 SmartIR 設定或更新 `codes/*/*.json` 裝置定義後，通常仍需要完整重新啟動 Home Assistant 才能保證新設定被讀入。這讓調整裝置碼、測試 IR 指令或微調 entity 綁定的迭代成本偏高，也不符合 SmartIR 這類高度依賴 YAML 與本地 JSON 的整合使用情境。

## What Changes

- 為 SmartIR 新增快速 reload 能力，讓使用者在不重啟整個 Home Assistant 的情況下，重新載入 SmartIR 相關 YAML platform。
- 重新載入時必須重新讀取 `configuration.yaml` 內的 SmartIR platform 設定，以及 `codes/climate/*.json`、`codes/fan/*.json`、`codes/light/*.json`、`codes/media_player/*.json` 內的裝置定義。
- 在 reload 流程中正確重建 SmartIR entities，避免遺留舊的 state listener、重複 callback 或失效 entity。
- 新增必要文件，說明哪些 SmartIR 變更可透過 reload 生效，哪些情況仍需完整重啟 Home Assistant。
- 不在此次變更中導入 Config Entry、Options Flow 或整合頁面的 Reload 機制。

## Capabilities

### New Capabilities
- `smartir-fast-reload`: 提供 SmartIR YAML 與 device JSON 的快速重新載入能力，降低調整與測試成本。

### Modified Capabilities

## Impact

- 主要影響 [custom_components/smartir/__init__.py](/home/seng96/ha/SmartIR/custom_components/smartir/__init__.py) 的整合初始化與 reload service 註冊邏輯。
- 主要影響 [custom_components/smartir/climate.py](/home/seng96/ha/SmartIR/custom_components/smartir/climate.py)、[custom_components/smartir/fan.py](/home/seng96/ha/SmartIR/custom_components/smartir/fan.py)、[custom_components/smartir/light.py](/home/seng96/ha/SmartIR/custom_components/smartir/light.py)、[custom_components/smartir/media_player.py](/home/seng96/ha/SmartIR/custom_components/smartir/media_player.py) 的 entity lifecycle 與監聽解除行為。
- 需要更新 [docs/README.md](/home/seng96/ha/SmartIR/docs/README.md) 與各平台文件，說明快速 reload 的使用方式與限制。
- 不應改變既有 SmartIR entity 的功能邏輯，也不應要求使用者改寫現有 YAML 配置格式。
