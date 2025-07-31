# 📑 綜合戰情簡報

**報告產生時間:** 2025-07-31 22:30:53 CST
**總耗時:** 0 分 1 秒

---

### 一、總體結果
**狀態:** <font color="red">執行完畢，但有錯誤發生</font>

### 二、效能重點
- **平均 CPU 使用率:** 0.0%
- **峰值 CPU 使用率:** 0.0%
- **平均記憶體使用率:** 8.0%
- **峰值記憶體使用率:** 8.0%

### 三、耗時最長任務 Top 5
| 任務名稱                   |   耗時 (秒) | 開始時間                         | 結束時間                         |
|:---------------------------|------------:|:---------------------------------|:---------------------------------|
| 安裝 main_dashboard 的依賴 |       0.505 | 2025-08-01 06:30:52.360000+08:00 | 2025-08-01 06:30:52.865000+08:00 |

### 四、關鍵事件摘要
- **[BATTLE]** 鳳凰之心 v19.0 [完整模式] 啟動序列開始。
- **[BATTLE]** 開始為 main_dashboard 安裝 17 個依賴。
- **[SUCCESS]** [main_dashboard] 所有依賴已成功安裝。
- **[CRITICAL]** 管理應用 'main_dashboard' 時發生嚴重錯誤: [Errno 2] No such file or directory: 'apps/main_dashboard/.venv/bin/gunicorn'
- **[CRITICAL]** 主儀表板 (main_dashboard) 啟動失敗: [Errno 2] No such file or directory: 'apps/main_dashboard/.venv/bin/gunicorn'，中止所有操作。