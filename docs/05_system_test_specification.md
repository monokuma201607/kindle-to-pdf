# システムテスト仕様書

| 項目 | 内容 |
|------|------|
| 文書番号 | TS-SYS-001 |
| バージョン | 1.0 |
| 作成日 | 2024-12-06 |
| 関連文書 | FS-KINDLE-001, TS-BDD-001 |

---

## 1. テスト概要

### 1.1 目的
システム全体の統合テストおよびE2Eテストを定義

### 1.2 テスト環境

| 項目 | 内容 |
|------|------|
| OS | Windows 10/11 |
| Python | 3.8+ |
| ブラウザ | Chrome (最新版) |
| テストツール | pytest, Selenium (E2E) |

---

## 2. テストケース一覧

### 2.1 機能テスト

| TC-ID | テスト名 | 前提条件 | 手順 | 期待結果 |
|-------|---------|---------|------|---------|
| TC-001 | UI起動確認 | サーバー起動 | http://localhost:5000 アクセス | メイン画面表示 |
| TC-002 | ウィンドウ検出 | Kindle起動 | API GET /api/status | found: true |
| TC-003 | キャプチャ開始 | ウィンドウ検出済 | POST /api/capture/start | status: started |
| TC-004 | 進捗更新 | キャプチャ中 | WebSocket接続 | progressイベント受信 |
| TC-005 | キャプチャ停止 | キャプチャ中 | POST /api/capture/stop | status: stopped |
| TC-006 | PDF生成確認 | キャプチャ完了 | ファイル確認 | PDFファイル存在 |
| TC-007 | 設定変更 | 設定画面表示 | PUT /api/config | 設定反映 |

### 2.2 異常系テスト

| TC-ID | テスト名 | 前提条件 | 手順 | 期待結果 |
|-------|---------|---------|------|---------|
| TC-101 | ウィンドウ未検出 | Kindle未起動 | キャプチャ開始 | E001エラー |
| TC-102 | 不正ページ数 | - | pages = -1 で開始 | バリデーションエラー |
| TC-103 | 二重開始防止 | キャプチャ中 | 再度開始 | 拒否レスポンス |

### 2.3 性能テスト

| TC-ID | テスト名 | 条件 | 期待結果 |
|-------|---------|------|---------|
| TC-201 | 起動時間 | コールドスタート | 3秒以内 |
| TC-202 | メモリ使用量 | 100ページキャプチャ | 500MB以下 |
| TC-203 | レスポンス時間 | API呼び出し | 200ms以内 |

---

## 3. E2Eテストシナリオ

### 3.1 基本フロー

```
1. アプリケーション起動
2. Kindle for PC起動・書籍表示
3. ブラウザで http://localhost:5000 アクセス
4. Kindle検出確認
5. 自動モード選択
6. 開始ボタンクリック
7. 進捗確認（プログレスバー更新）
8. 完了まで待機
9. PDF生成確認
10. PDFファイルを開いて内容確認
```

### 3.2 テストコード概要

```python
# tests/system/test_e2e.py

class TestE2E:
    def test_full_capture_flow(self, app_client, mock_kindle):
        """完全なキャプチャフローをテスト"""
        # 1. 状態確認
        response = app_client.get('/api/status')
        assert response.json['kindle_found'] == True
        
        # 2. キャプチャ開始
        response = app_client.post('/api/capture/start', json={
            'mode': 'fixed',
            'pages': 3,
            'output_filename': 'test.pdf'
        })
        assert response.json['status'] == 'started'
        
        # 3. 完了待機
        # WebSocketで完了イベントを待機
        
        # 4. PDF確認
        assert Path('test.pdf').exists()
```

---

## 4. テスト実行手順

```powershell
# 1. 依存パッケージインストール
pip install -r requirements-dev.txt

# 2. ユニットテスト
pytest tests/test_unit.py -v

# 3. BDDテスト
pytest tests/step_defs/ -v

# 4. システムテスト（E2E）
pytest tests/system/ -v

# 5. 全テスト + カバレッジ
pytest tests/ -v --cov=kindle_capture --cov=web
```

---

## 5. 合格基準

| 項目 | 基準 |
|------|------|
| テストパス率 | 100% |
| コードカバレッジ | 80%以上 |
| 重大バグ | 0件 |
