# 楽天市場API検索ツール

## 使用方法

1. 楽天APIのアプリケーションIDを取得
   - https://webservice.rakuten.co.jp/ でアカウント作成
   - アプリIDを取得

2. 環境変数の設定
   - `.env.example`を`.env`にコピー
   - `.env`ファイル内の`RAKUTEN_APP_ID`に実際のアプリIDを設定

3. Python仮想環境のセットアップ
   ```bash
   # 仮想環境の作成
   python3 -m venv venv
   
   # 仮想環境の有効化
   source venv/bin/activate  # macOS/Linux
   # または
   venv\Scripts\activate  # Windows
   ```

4. 必要なライブラリをインストール
   ```bash
   pip install -r requirements.txt
   ```

5. 実行
   ```bash
   python rakuten_search.py
   ```

## 機能
- キーワード検索
- 上位5件の商品情報取得
- 商品名、価格、ショップ名、レビュー情報、商品説明、URLの表示
- 商品画像URL（トップ画像）の表示