## Context

SmartIR 目前是典型的 Home Assistant YAML platform 整合：根模組 [`custom_components/smartir/__init__.py`](/home/seng96/ha/SmartIR/custom_components/smartir/__init__.py) 只處理整合層級設定與 service 註冊，各實體則分散在 [`custom_components/smartir/climate.py`](/home/seng96/ha/SmartIR/custom_components/smartir/climate.py)、[`custom_components/smartir/fan.py`](/home/seng96/ha/SmartIR/custom_components/smartir/fan.py)、[`custom_components/smartir/light.py`](/home/seng96/ha/SmartIR/custom_components/smartir/light.py)、[`custom_components/smartir/media_player.py`](/home/seng96/ha/SmartIR/custom_components/smartir/media_player.py) 的 `async_setup_platform()` 中建立。每個平台 setup 時都會從磁碟讀取對應的 `codes/<platform>/*.json` 裝置定義，因此只要平台能被乾淨地 reset 並重新 setup，就有機會在不重啟 Home Assistant 的前提下吃到最新 YAML 與 JSON。

這次變更是跨模組的，因為 reload 入口在整合根模組，但真正要被重建的是四個 entity platform；同時 `climate`、`fan`、`light` 目前都在 `async_added_to_hass()` 內註冊 sensor state listener，卻沒有明確把 unsubscribe callback 綁到 entity 移除 lifecycle。若直接加入 reload 而不補這塊，舊 entity 雖然會被 platform reset 移除，事件監聽卻可能殘留，導致重複 callback、已移除 entity 仍收到事件，或在多次 reload 後出現狀態異常。

本設計的限制也很明確：SmartIR 仍維持 YAML-only 模式，不導入 Config Entry，也不追求 Home Assistant「整合頁面」那種 entry-based reload。此次只處理 SmartIR 自己可掌控的 YAML platform 與本地 device JSON 載入鏈路。

## Goals / Non-Goals

**Goals:**
- 提供一條 SmartIR 專用的 reload 路徑，能在不重啟整個 HA 的情況下重載 SmartIR 四個 YAML platform。
- 讓 reload 流程重新讀取最新 `configuration.yaml` 與 `codes/*/*.json`，而不是重用舊的記憶體內狀態。
- 確保 entity 在 reload / reset 過程中正確解除 listener 與 callback，避免多次 reload 後累積副作用。
- 保持既有 YAML 配置格式與 entity 行為向後相容，讓現有使用者只多一個 reload 能力，不需改寫設定。

**Non-Goals:**
- 不導入 Config Flow、Options Flow、`async_setup_entry` 或 `async_unload_entry`。
- 不把 SmartIR 改造成可以從「設定 > 裝置與服務 > 整合」頁面直接 Reload 的架構。
- 不變更 controller 傳輸協定、IR code JSON schema 或各平台既有功能邏輯。
- 不承諾所有 Home Assistant 核心設定都能透過 SmartIR reload 生效；僅針對 SmartIR 相關 YAML 與 device JSON 變更提供保證。

## Decisions

### 1. 以 `homeassistant.helpers.reload.async_setup_reload_service` 建立 SmartIR reload 入口

決策：在 [`custom_components/smartir/__init__.py`](/home/seng96/ha/SmartIR/custom_components/smartir/__init__.py) 的 `async_setup()` 中註冊 SmartIR 專用 reload service，目標平台固定為 `climate`、`fan`、`light`、`media_player`。

理由：
- SmartIR 目前就是 YAML platform 整合，Home Assistant 已提供對這類整合最接近需求的標準 helper。
- 這條路徑會在 reload 時重新處理 YAML，並對既有 entity platform 執行 reset + setup，剛好符合 SmartIR 需求。
- 改動集中在整合入口，能最大限度保留現有平台實作。

替代方案：
- 自行實作自訂 service，手動遍歷 entity platform 並重建。可行，但會重複 Home Assistant 既有 reload 流程，維護成本較高。
- 轉為 Config Entry。從長期產品演進來看更現代，但範圍遠大於此次需求，且會牽動使用方式與資料模型。

### 2. 依賴「平台重新 setup 時重讀磁碟」來支援 `codes/*/*.json` 更新

決策：不新增額外的 JSON cache invalidation 層，而是延用各平台 `async_setup_platform()` 既有的讀檔流程，讓 reload 透過重跑 platform setup 來重讀最新 device JSON。

理由：
- `climate` 已經在 setup 期間動態解析裝置碼路徑；其他平台也在 setup 時從磁碟讀檔。
- 保持載入責任集中於各平台，避免在根模組加入跨平台 cache 管理，降低耦合。
- 這種設計天然對齊使用者心智模型：改檔後 reload，entity 用新檔重建。

替代方案：
- 在根模組維護裝置碼快取並於 reload 時清空。這會增加共享狀態與一致性問題，對目前專案沒有明顯收益。

### 3. 所有事件監聽都必須改為由 entity lifecycle 擁有

決策：`climate`、`fan`、`light` 透過 `async_track_state_change_event()` 建立的監聽，都必須把 unsubscribe callback 用 `self.async_on_remove(...)` 掛到 entity lifecycle；必要時補 `async_will_remove_from_hass()` 只做輔助清理，不自行管理多套狀態。

理由：
- 這是讓 `EntityPlatform.async_reset()` 安全運作的關鍵。只要 entity 被正確移除，舊 listener 就會一起解除。
- 比起自管 unsubscribe list，使用 `self.async_on_remove(...)` 更貼近 HA entity 模型，也較不容易漏清理。
- 可以同時修補現有初始化不一致問題，例如 `fan` 的 power sensor listener 註冊不該依賴 `last_state is not None`。

替代方案：
- 手動在每個 entity 類別維護 listener handle list，並在 `async_will_remove_from_hass()` 逐一呼叫。雖然也可行，但比 `self.async_on_remove(...)` 冗長且更容易出錯。

### 4. Reload 範圍限定為 SmartIR 管理的平台，不擴大到其他依賴整合

決策：reload 只重設 SmartIR 在 `climate`、`fan`、`light`、`media_player` 建立的 entities，不主動 reload 其他 controller 相關整合，例如 Broadlink、MQTT 或 ESPHome。

理由：
- SmartIR 對這些 controller 的依賴是 runtime service 呼叫，而非它們的配置所有者；擴大 reload 範圍會變成跨整合協調問題。
- 使用者這次要的是 SmartIR 自身設定與 codes 變更快速生效，不是整個 HA 生態的一鍵重載。

替代方案：
- 在文件中暗示需要同步 reload 其他 controller。這不是 SmartIR 能保證的能力，因此只適合文件說明限制，不適合做進核心設計。

### 5. 文件需明確區分「SmartIR reload 可生效」與「仍需 HA 重啟」的邊界

決策：在 [`docs/README.md`](/home/seng96/ha/SmartIR/docs/README.md) 為主文件補一段快速 reload 說明，平台文件則只補充適用範圍與限制，不分散成多套操作指引。

理由：
- 使用者主要問題是「哪些改動可以不用整個 HA 重啟」，這需要集中說明。
- README 作為入口最適合放操作步驟，平台文件則保留平台特定的配置說明。

替代方案：
- 各平台文件都各自寫一套 reload 指引。資訊會重複，且日後調整容易失同步。

## Risks / Trade-offs

- [平台 reset 後仍殘留舊 listener] → 先全面改成 `self.async_on_remove(...)` 綁定 unsubscribe，再驗證多次 reload。
- [各平台初始化行為不一致，reload 後狀態與冷啟動不同] → 盤點 `async_added_to_hass()` 的初始化條件，特別修正 `fan` 目前只在有 restore state 時才註冊 power sensor 監聽的問題。
- [使用者誤以為所有 YAML 變更都能透過 SmartIR reload 生效] → 在 README 明確標示僅保證 SmartIR 相關 platform 與 device JSON，其他 HA 核心設定仍可能需要重啟。
- [reload 中途讀到無效 JSON 或錯誤 YAML，造成部分 entity 未建立] → 延續平台既有的錯誤處理，讓失敗平台記錄 log 並不中斷整個 HA；文件中也需提醒先檢查配置。
- [未來若專案改成 Config Entry，這套 reload 設計需重做] → 在設計上把 reload 視為 YAML-only 時代的最小解，避免過度抽象化，將來若遷移再整體改寫。
