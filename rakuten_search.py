import requests
import json
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime

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
    
    def read_keywords_from_sheet(self, sheet_name: str = "キーワード") -> List[Dict]:
        """
        キーワードシートのA列からキーワードを読み取り
        
        Args:
            sheet_name: シート名（デフォルト: キーワードシート）
        
        Returns:
            キーワードと行番号の辞書リスト
        """
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:B"
            ).execute()
            
            values = result.get('values', [])
            keywords_data = []
            
            # 1行目はヘッダー行なのでスキップ
            for i, row in enumerate(values[1:], start=2):
                if row and row[0].strip():  # キーワードが空でない場合
                    keyword = row[0].strip()
                    # B列に「完了」フラグがない場合のみ追加
                    flag = row[1].strip() if len(row) > 1 else ""
                    if flag != "完了":
                        keywords_data.append({
                            'keyword': keyword,
                            'row': i
                        })
            
            return keywords_data
            
        except Exception as e:
            print(f"キーワードシート読み取りエラー: {e}")
            return []
    
    def read_keywords(self, sheet_name: str = "キーワード") -> List[str]:
        """
        キーワードシートからキーワードを読み取り（後方互換性のため残す）
        
        Args:
            sheet_name: シート名（デフォルト: キーワードシート）
        
        Returns:
            キーワードのリスト
        """
        keywords_data = self.read_keywords_from_sheet(sheet_name)
        return [item['keyword'] for item in keywords_data]
    
    def update_search_flag(self, sheet_name: str, row: int) -> bool:
        """
        キーワードシートの検索完了フラグを更新
        
        Args:
            sheet_name: シート名
            row: 更新する行番号
        
        Returns:
            成功時True、失敗時False
        """
        try:
            range_name = f"{sheet_name}!B{row}"
            body = {'values': [["完了"]]}
            
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
    
    def write_to_results_sheet(self, results: List[Dict], sheet_name: str = "検索結果") -> bool:
        """
        検索結果シートに結果を書き込み（新しい行を追加）
        
        Args:
            results: 検索結果のリスト
            sheet_name: シート名（デフォルト: 検索結果シート）
        
        Returns:
            成功時True、失敗時False
        """
        try:
            # ヘッダー行を準備
            headers = [
                '取得日時', 'キーワード', '順位', '商品名', '価格', 'ショップ名', 
                'レビュー平均', 'レビュー数', '商品URL', '画像URL', '商品説明'
            ]
            
            sheet = self.service.spreadsheets()
            
            # シートの現在のデータを確認（ヘッダーがあるかチェック）
            try:
                result = sheet.values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{sheet_name}!A1:K1"
                ).execute()
                has_header = bool(result.get('values', []))
            except:
                has_header = False
            
            # データを準備
            data = []
            
            # ヘッダーがない場合は追加
            if not has_header:
                data.append(headers)
            
            # 現在の日時を取得
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 検索結果データを追加
            for result in results:
                for item in result['items']:
                    row = [
                        current_time,
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
            
            if data:
                # append APIを使用して新しい行を追加
                body = {'values': data}
                
                sheet.values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{sheet_name}!A:K",
                    valueInputOption='RAW',
                    insertDataOption='INSERT_ROWS',
                    body=body
                ).execute()
            
            return True
            
        except Exception as e:
            print(f"検索結果シート書き込みエラー: {e}")
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
                    'description': item['Item']['itemCaption']
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
        
        # キーワードシートからキーワードを読み取り
        print("キーワードシートからキーワードを読み取り中...")
        keywords_data = sheets_api.read_keywords_from_sheet("キーワード")
        
        if not keywords_data:
            print("キーワードが見つかりませんでした。")
            print("キーワードシートのA列（2行目以降）にキーワードを追加してください。")
            return
        
        keywords = [item['keyword'] for item in keywords_data]
        print(f"{len(keywords)}個のキーワードが見つかりました: {keywords}")
        
        # 各キーワードで検索を実行
        all_results = []
        for i, keyword_data in enumerate(keywords_data, 1):
            keyword = keyword_data['keyword']
            
            print(f"\n[{i}/{len(keywords_data)}] 「{keyword}」で検索中...")
            items = rakuten_api.search_items(keyword, hits=5)
            
            if items:
                all_results.append({
                    'keyword': keyword,
                    'items': items,
                    'row': keyword_data['row']
                })
                print(f"  {len(items)}件の商品が見つかりました")
            else:
                print(f"  検索結果が見つかりませんでした")
                # 検索結果がなくても行番号を記録
                all_results.append({
                    'keyword': keyword,
                    'items': [],
                    'row': keyword_data['row']
                })
        
        # 結果を検索結果シートに書き込み
        if all_results:
            print(f"\n検索結果を検索結果シートに書き込み中...")
            
            # 検索結果があるもののみ書き込み
            results_with_items = [r for r in all_results if r['items']]
            if results_with_items and sheets_api.write_to_results_sheet(results_with_items, "検索結果"):
                print("検索結果の書き込みが完了しました！")
                print(f"合計 {sum(len(r['items']) for r in results_with_items)} 件の商品情報を書き込みました。")
            elif results_with_items:
                print("書き込みに失敗しました。")
            else:
                print("検索結果がありませんでした。")
            
            # 検索完了フラグを更新
            print("\n検索完了フラグを更新中...")
            success_count = 0
            for result in all_results:
                if sheets_api.update_search_flag("キーワード", result['row']):
                    success_count += 1
            print(f"{success_count}/{len(all_results)}個のフラグを更新しました。")
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