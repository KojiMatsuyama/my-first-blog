import csv
import json

def convert_csv_to_json(csv_file_path, json_file_path):
    with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # 1行目 (Recognition,) をスキップ

        # フィールド名リストを作成
        fields = []
        field_id = 1
        for row in reader:
            if row and row[1]:  # 空行を除外し、2列目のデータがある場合のみ処理
                fields.append

