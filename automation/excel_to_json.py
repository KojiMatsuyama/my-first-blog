import pandas as pd
import json

def excel_to_json(excel_file_path, json_file_path):
    # Excelファイルを読み込み
    df = pd.read_excel(excel_file_path)

    # DataFrameをJSON形式に変換
    json_data = df.to_json(orient='records', force_ascii=False, indent=4)

    # JSONデータをファイルに保存
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json_file.write(json_data)

    print(f"JSONファイルを作成しました: {json_file_path}")
