import requests
import json
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

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


def main():
    # .envファイルから環境変数を読み込み
    load_dotenv()
    
    # 楽天APIのアプリケーションIDを環境変数から取得
    APP_ID = os.getenv('RAKUTEN_APP_ID')
    
    if not APP_ID:
        print("エラー: RAKUTEN_APP_IDが設定されていません。")
        print(".envファイルにRAKUTEN_APP_IDを設定してください。")
        return
    
    # APIクライアントを初期化
    api = RakutenSearchAPI(APP_ID)
    
    # 検索キーワードを入力
    keyword = input("検索キーワードを入力してください: ")
    
    # 商品を検索
    print(f"\n「{keyword}」で検索中...")
    items = api.search_items(keyword, hits=5)
    
    # 結果を表示
    if items:
        api.display_results(items)
    else:
        print("検索結果を取得できませんでした。")


if __name__ == "__main__":
    main()