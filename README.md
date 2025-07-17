# 楽天市場API検索ツール

楽天市場APIを使用した商品検索ツールです。キーワードベースの検索と、Google Sheetsとの連携による一括検索に対応しています。

## 機能

### 1. 手動検索
- キーワードを入力して楽天市場の商品を検索
- 上位5件の商品情報を表示

### 2. Google Sheets連携
- 「キーワード」シートのA列からキーワードを一括読み取り
- 各キーワードで自動検索を実行
- 「検索結果」シートに結果を自動書き込み
- **重複防止機能**: B列の検索完了フラグで処理済みキーワードをスキップ
- **履歴機能**: 取得日時を記録し、価格や順位の変動を追跡可能

### 取得できる商品情報
- 取得日時
- 商品名
- 価格
- ショップ名
- レビュー評価・件数
- 商品説明（全文）
- 商品URL
- 商品画像URL

## セットアップ

### 1. 楽天APIの設定
1. [楽天ウェブサービス](https://webservice.rakuten.co.jp/)でアカウント作成
2. アプリケーションIDを取得

### 2. Google Sheets API設定（一括検索を使う場合）
1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクト作成
2. Google Sheets APIを有効化
3. サービスアカウントを作成
4. 認証用JSONファイルをダウンロードして`credentials.json`として保存
5. Google Sheetsでスプレッドシートを作成
6. サービスアカウントのメールアドレスにスプレッドシートの編集権限を付与

### 3. 環境変数の設定
```bash
# .env.exampleを.envにコピー
cp .env.example .env
```

`.env`ファイルを編集：
```bash
# 楽天API設定
RAKUTEN_APP_ID=your_application_id_here

# Google Sheets API設定（一括検索を使う場合）
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEETS_ID=your_spreadsheet_id_here
```

### 4. Python環境の準備
```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

## 使用方法

### 基本実行
```bash
python rakuten_search.py
```

実行すると以下の選択画面が表示されます：
```
楽天商品検索ツール
1. 手動でキーワードを入力して検索
2. Google Sheetsからキーワードを読み取って一括検索
選択してください (1 or 2):
```

### Google Sheets一括検索の設定

#### 1. キーワードシート
シート名: 「キーワード」

| A列 | B列 |
|-----|-----|
| キーワード | 検索完了フラグ |
| iPhone | 完了 |
| ノートパソコン | |
| コーヒー | |

- **1行目**: ヘッダー行（A1: キーワード、B1: 検索完了フラグ）
- **2行目以降**: 検索したいキーワードを入力
- **B列**: 検索完了時に自動で「完了」が記入される

#### 2. 検索結果シート
シート名: 「検索結果」

| 取得日時 | キーワード | 順位 | 商品名 | 価格 | ショップ名 | レビュー平均 | レビュー数 | 商品URL | 画像URL | 商品説明 |
|---------|----------|------|--------|------|-----------|------------|----------|---------|---------|---------|
| 2024-01-20 10:30:00 | iPhone | 1 | iPhone 15 Pro... | 159,800 | Apple Store | 4.8 | 250 | https://... | https://... | 最新のiPhone... |

- **ヘッダー行は自動生成**: 初回実行時に自動で作成される
- **新規追加方式**: 実行のたびに新しい行が追加される（既存データは保持）
- **取得日時**: 検索実行時の日時が自動記録される

## プロジェクト構成

```
.
├── rakuten_search.py     # メインアプリケーション
├── requirements.txt      # Python依存関係
├── .env.example         # 環境変数テンプレート
├── .env                # 環境変数設定（gitignore済み）
├── credentials.json    # Google Sheets認証ファイル（gitignore済み）
└── README.md           # このファイル
```

## 注意事項

- `credentials.json`と`.env`ファイルは機密情報を含むため、バージョン管理には含まれません
- Google Sheets APIには利用制限があります（100リクエスト/100秒/ユーザー）
- 楽天APIにも利用制限があります（詳細は楽天API仕様書を確認）