import json
import traceback
from django.db import transaction
from .admin import Schema, SchemaFields

def import_schema_from_json(json_data):
    try:
        print("[INFO] JSONデータの読み込み開始")

        # JSONデータをPythonオブジェクトに変換
        schema_data = json.loads(json_data)
        print(f"[DEBUG] 解析されたJSONデータ: {schema_data}")

        # JSONデータが期待した形式であるか確認
        if not isinstance(schema_data, dict) or 'schema' not in schema_data or 'fields' not in schema_data:
            print("[ERROR] JSONデータの形式が不正です。")
            return "JSONデータの形式が不正です"

        schema_info = schema_data['schema']
        fields = schema_data['fields']

        with transaction.atomic():
            print("[INFO] データベーストランザクション開始")

            # Schemaを更新または作成
            schema_obj, schema_created = Schema.objects.update_or_create(
                id=schema_info['id'],
                defaults={
                    'name': schema_info['name'],
                    'description': schema_info.get('description', '')
                }
            )
            print(f"[INFO] Schema: {schema_obj.name} を{'追加' if schema_created else '更新'}しました。")

            # SchemaFieldを処理
            for index, field in enumerate(fields):
                try:
                    print(f"[DEBUG] {index + 1} 件目のデータを処理中: {field}")

                    # 必須フィールドの確認
                    required_keys = ['id', 'field_name', 'field_type']
                    if not all(key in field for key in required_keys):
                        print(f"[ERROR] 必須フィールドが不足しています: {field}")
                        continue

                    # SchemaFieldの更新または作成
                    field_obj, field_created = SchemaFields.objects.update_or_create(
                        id=field['id'],
                        schema=schema_obj,
                        defaults={
                            'name': field['field_name'],
                            'field_type': field['field_type'],
                            'is_required': field.get('is_required', False),
                            'choices': field.get('choices', '')
                        }
                    )
                    action = "追加" if field_created else "更新"
                    print(f"[INFO] Field: {field_obj.name} を{action}しました。")

                except Exception as field_error:
                    print(f"[ERROR] {index + 1} 件目でエラー発生: {field}")
                    traceback.print_exc()
                    raise field_error

            print("[INFO] データベーストランザクション完了")

    except Exception as e:
        print("[CRITICAL] インポート処理中に予期せぬエラーが発生しました。")
        traceback.print_exc()
        return "インポート中にエラーが発生しました。"

    return "インポート完了"
