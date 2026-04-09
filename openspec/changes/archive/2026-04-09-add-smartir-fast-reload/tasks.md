## 1. Reload 能力設計與接線

- [x] 1.1 在 `custom_components/smartir/__init__.py` 建立 SmartIR 專用的 reload 流程，能重新載入 `climate`、`fan`、`light`、`media_player` 四個平台。
- [x] 1.2 確認 reload 流程會重新處理最新的 YAML 設定，而不是重用舊的 in-memory config。
- [x] 1.3 確認 reload 流程會重跑各平台的 setup，使 platform 重新讀取對應的 `codes/*/*.json` 檔案。

## 2. Entity Lifecycle 與監聽清理

- [x] 2.1 盤點並修正 `climate`、`fan`、`light` 中透過 `async_track_state_change_event` 建立的監聽，確保 entity 移除時會正確解除註冊。
- [x] 2.2 確認 platform reset / reload 後不會殘留重複 listener、雙重 callback 或已移除 entity 的事件處理。
- [x] 2.3 修正任何會讓 reload 後 entity 行為與首次啟動不一致的初始化邏輯。

## 3. 文件更新

- [x] 3.1 更新 `docs/README.md`，說明 SmartIR 的快速 reload 用途、適用範圍與基本操作方式。
- [x] 3.2 更新相關平台文件，說明 `configuration.yaml` 或 `codes/*.json` 變更後何時可用 reload 生效、何時仍需重啟 HA。

## 4. 驗證

- [x] 4.1 驗證修改 SmartIR 的 YAML platform 設定後，透過 reload 可重新建立 entities 並套用新設定。
- [x] 4.2 驗證修改 `codes` 目錄中的 device JSON 後，透過 reload 可讓 entity 讀到更新後的裝置定義。
- [x] 4.3 驗證 reload 多次後不會出現 listener 累積、重複事件處理或 entity 移除錯誤。
- [x] 4.4 驗證未修改 SmartIR 以外設定時，reload 不會影響其他非 SmartIR 平台的既有行為。
