import requests
import json
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

class GoogleSheetsAPI:
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        """
        Google Sheets APIクラス
        
        Args:
            credentials_file: サービスアカウントのJSONファイルパス
            spreadsheet_id: Google SheetsのID
        """
        self.spreadsheet_id = spreadsheet_id
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.credentials = Credentials.from_service_account_file(
            credentials_file, scopes=self.scopes
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
    
    def read_keywords_with_flags(self, range_name: str = "A:B") -> List[Dict]:
        """
        スプレッドシートからキーワードとフラグを読み取り
        
        Args:
            range_name: 読み取る範囲（デフォルト: A列とB列）
        
        Returns:
            キーワードと行番号、フラグ状態の辞書リスト
        """
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            keywords_data = []
            
            for i, row in enumerate(values, start=1):
                if row and row[0].strip():  # キーワードが空でない場合
                    keyword = row[0].strip()
                    flag = row[1].strip() if len(row) > 1 else ""
                    
                    # フラグが"完了"でない場合のみ追加
                    if flag != "完了":
                        keywords_data.append({
                            'keyword': keyword,
                            'row': i,
                            'flag': flag
                        })
            
            return keywords_data
            
        except Exception as e:
            print(f"スプレッドシート読み取りエラー: {e}")
            return []
    
    def read_keywords(self, range_name: str = "A:A") -> List[str]:
        """
        スプレッドシートからキーワードを読み取り（後方互換性のため残す）
        
        Args:
            range_name: 読み取る範囲（デフォルト: A列全体）
        
        Returns:
            キーワードのリスト
        """
        keywords_data = self.read_keywords_with_flags("A:B")
        return [item['keyword'] for item in keywords_data]
    
    def update_flag(self, row: int, flag_value: str = "完了") -> bool:
        """
        特定の行のフラグを更新
        
        Args:
            row: 更新する行番号
            flag_value: 設定するフラグ値（デフォルト: "完了"）
        
        Returns:
            成功時True、失敗時False
        """
        try:
            range_name = f"B{row}"
            body = {'values': [[flag_value]]}
            
            sheet = self.service.spreadsheets()
            sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"フラグ更新エラー: {e}")
            return False

    def write_search_results(self, results: List[Dict], start_row: int = 1) -> bool:
        """
        検索結果をスプレッドシートに書き込み
        
        Args:
            results: 検索結果のリスト
            start_row: 書き込み開始行
        
        Returns:
            成功時True、失敗時False
        """
        try:
            # ヘッダー行を準備
            headers = [
                'キーワード', '順位', '商品名', '価格', 'ショップ名', 
                'レビュー平均', 'レビュー数', '商品URL', '画像URL', '商品説明'
            ]
            
            # データを準備
            data = [headers]
            for result in results:
                for item in result['items']:
                    row = [
                        result['keyword'],
                        item['rank'],
                        item['name'],
                        item['price'],
                        item['shop_name'],
                        item['review_average'],
                        item['review_count'],
                        item['url'],
                        item['image_url'],
                        item['description']
                    ]
                    data.append(row)
            
            # スプレッドシートに書き込み
            range_name = f"C{start_row}:L{start_row + len(data) - 1}"
            body = {'values': data}
            
            sheet = self.service.spreadsheets()
            sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"スプレッドシート書き込みエラー: {e}")
            return False

class RakutenSearchAPI:
    def __init__(self, app_id: str):
        """
        楽天市場API検索クラス
        
        Args:
            app_id: 楽天APIのアプリケーションID
        """
        self.app_id = app_id
        self.base_url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"
    
    def search_items(self, keyword: str, hits: int = 5) -> Optional[List[Dict]]:
        """
        指定したキーワードで商品を検索
        
        Args:
            keyword: 検索キーワード
            hits: 取得する商品数（デフォルト: 5）
        
        Returns:
            商品情報のリスト
        """
        params = {
            'applicationId': self.app_id,
            'keyword': keyword,
            'hits': hits,
            'sort': 'standard',
            'format': 'json'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Items' not in data:
                print("検索結果が見つかりませんでした。")
                return None
            
            items = []
            for item in data['Items']:
                # 商品画像URLを取得（最初の画像URL）
                image_url = ''
                if 'mediumImageUrls' in item['Item'] and item['Item']['mediumImageUrls']:
                    image_url = item['Item']['mediumImageUrls'][0]['imageUrl']
                
                item_info = {
                    'rank': len(items) + 1,
                    'name': item['Item']['itemName'],
                    'price': item['Item']['itemPrice'],
                    'shop_name': item['Item']['shopName'],
                    'url': item['Item']['itemUrl'],
                    'image_url': image_url,
                    'review_count': item['Item']['reviewCount'],
                    'review_average': item['Item']['reviewAverage'],
                    'description': item['Item']['itemCaption'][:100] + '...' if len(item['Item']['itemCaption']) > 100 else item['Item']['itemCaption']
                }
                items.append(item_info)
            
            return items
            
        except requests.exceptions.RequestException as e:
            print(f"APIリクエストエラー: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSONデコードエラー: {e}")
            return None
        except Exception as e:
            print(f"予期しないエラー: {e}")
            return None
    
    def display_results(self, items: List[Dict]) -> None:
        """
        検索結果を表示
        
        Args:
            items: 商品情報のリスト
        """
        if not items:
            return
        
        print(f"\n検索結果 上位{len(items)}件:")
        print("=" * 80)
        
        for item in items:
            print(f"\n【{item['rank']}位】")
            print(f"商品名: {item['name']}")
            print(f"価格: ¥{item['price']:,}")
            print(f"ショップ: {item['shop_name']}")
            print(f"レビュー: ★{item['review_average']} ({item['review_count']}件)")
            if item['image_url']:
                print(f"画像URL: {item['image_url']}")
            print(f"商品説明: {item['description']}")
            print(f"URL: {item['url']}")
            print("-" * 80)


def search_from_spreadsheet():
    """
    Google Sheetsからキーワードを読み取って楽天APIで検索し、結果をスプレッドシートに書き込む
    """
    # .envファイルから環境変数を読み込み
    load_dotenv()
    
    # 環境変数から設定を取得
    RAKUTEN_APP_ID = os.getenv('RAKUTEN_APP_ID')
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
    GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
    
    # 必要な設定の確認
    if not RAKUTEN_APP_ID:
        print("エラー: RAKUTEN_APP_IDが設定されていません。")
        return
    
    if not GOOGLE_SHEETS_CREDENTIALS_FILE:
        print("エラー: GOOGLE_SHEETS_CREDENTIALS_FILEが設定されていません。")
        return
    
    if not GOOGLE_SHEETS_ID:
        print("エラー: GOOGLE_SHEETS_IDが設定されていません。")
        return
    
    if not os.path.exists(GOOGLE_SHEETS_CREDENTIALS_FILE):
        print(f"エラー: 認証ファイル '{GOOGLE_SHEETS_CREDENTIALS_FILE}' が見つかりません。")
        return
    
    try:
        # APIクライアントを初期化
        sheets_api = GoogleSheetsAPI(GOOGLE_SHEETS_CREDENTIALS_FILE, GOOGLE_SHEETS_ID)
        rakuten_api = RakutenSearchAPI(RAKUTEN_APP_ID)
        
        # スプレッドシートからキーワードとフラグを読み取り
        print("スプレッドシートからキーワードを読み取り中...")
        keywords_data = sheets_api.read_keywords_with_flags()
        
        if not keywords_data:
            print("未処理のキーワードが見つかりませんでした。")
            print("新しいキーワードを追加するか、既存のフラグを削除してください。")
            return
        
        keywords = [item['keyword'] for item in keywords_data]
        print(f"{len(keywords)}個の未処理キーワードが見つかりました: {keywords}")
        
        # 各キーワードで検索を実行
        all_results = []
        for i, keyword_data in enumerate(keywords_data, 1):
            keyword = keyword_data['keyword']
            row = keyword_data['row']
            
            print(f"\n[{i}/{len(keywords_data)}] 「{keyword}」で検索中...")
            items = rakuten_api.search_items(keyword, hits=5)
            
            if items:
                all_results.append({
                    'keyword': keyword,
                    'items': items,
                    'row': row
                })
                print(f"  {len(items)}件の商品が見つかりました")
            else:
                print(f"  検索結果が見つかりませんでした")
                # 検索結果がなくてもフラグを更新（重複実行を防ぐため）
                all_results.append({
                    'keyword': keyword,
                    'items': [],
                    'row': row
                })
        
        # 結果をスプレッドシートに書き込みとフラグ更新
        if all_results:
            print(f"\n検索結果をスプレッドシートに書き込み中...")
            
            # 検索結果があるもののみ書き込み
            results_with_items = [r for r in all_results if r['items']]
            if results_with_items and sheets_api.write_search_results(results_with_items):
                print("検索結果の書き込みが完了しました！")
            elif results_with_items:
                print("書き込みに失敗しました。")
            
            # 全てのキーワードのフラグを更新（検索済みマーク）
            print("処理済みフラグを更新中...")
            success_count = 0
            for result in all_results:
                if sheets_api.update_flag(result['row']):
                    success_count += 1
            
            print(f"{success_count}/{len(all_results)}個のフラグを更新しました")
            
        else:
            print("処理する検索結果がありません。")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")

def main():
    """
    メイン関数 - 手動検索またはスプレッドシート検索を選択
    """
    # .envファイルから環境変数を読み込み
    load_dotenv()
    
    print("楽天商品検索ツール")
    print("1. 手動でキーワードを入力して検索")
    print("2. Google Sheetsからキーワードを読み取って一括検索")
    
    choice = input("選択してください (1 or 2): ").strip()
    
    if choice == "1":
        # 従来の手動検索
        RAKUTEN_APP_ID = os.getenv('RAKUTEN_APP_ID')
        
        if not RAKUTEN_APP_ID:
            print("エラー: RAKUTEN_APP_IDが設定されていません。")
            return
        
        api = RakutenSearchAPI(RAKUTEN_APP_ID)
        keyword = input("検索キーワードを入力してください: ")
        
        print(f"\n「{keyword}」で検索中...")
        items = api.search_items(keyword, hits=5)
        
        if items:
            api.display_results(items)
        else:
            print("検索結果を取得できませんでした。")
            
    elif choice == "2":
        # スプレッドシート検索
        search_from_spreadsheet()
    else:
        print("無効な選択です。1または2を入力してください。")


if __name__ == "__main__":
    main()