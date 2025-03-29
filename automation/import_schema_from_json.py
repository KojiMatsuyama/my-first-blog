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

        # JSONデータがリストの場合、最初の要素を取得
        if isinstance(schema_data, list) and len(schema_data) > 0:
            schema_data = schema_data[0]
        else:
            print("[ERROR] JSONデータの形式が不正です。（期待されたリスト形式ではありません）")
            return "JSONフォーマットエラー"

        # 必要なキーが存在するかチェック
        if "schema" not in schema_data or "fields" not in schema_data:
            print("[ERROR] JSONデータの形式が不正です。（schema または fields キーがありません）")
            return "JSONフォーマットエラー"


        # JSONデータが期待した形式であるか確認
        if not isinstance(schema_data, dict) or 'schema' not in schema_data or 'fields' not in schema_data:
            print("[ERROR] JSONデータの形式が不正です。")
            return "JSONデータの形式が不正です"

        schema_info = schema_data['schema']
        fields = schema_data['fields']

        with transaction.atomic():
            print("[INFO] データベーストランザクション開始")

            # デバッグ: schema_infoのidとnameを表示
            print(f"[DEBUG] インポート対象のSchema ID: {schema_info['id']}")
            print(f"[DEBUG] インポート対象のSchema Name: {schema_info['name']}")

            # update_or_createの前にidとdefaultsの内容をデバッグ
            print(f"[DEBUG] update_or_create 実行前:")
            print(f"  ID: {schema_info['id']}")
            print(f"  defaults: {{'name': {schema_info['name']}, 'description': {schema_info.get('description', '')}}}")

            # Schemaの更新または作成
            schema_obj, schema_created = Schema.objects.update_or_create(
                name=schema_info['name'],
                defaults={
                    'name': schema_info['name'],
                    'description': schema_info.get('description', '')
                }
            )
            print(f"[INFO] Schema: {schema_obj.name} を{'追加' if schema_created else '更新'}しました。")

            # 既存のSchemaFieldを削除
            print(f"[INFO] Schema ID {schema_info['id']} に関連する全てのフィールドを削除します。")
            SchemaFields.objects.filter(schema_id=schema_info['id']).delete()

            # SchemaFieldを処理


            for index, field in enumerate(fields):
                try:
                    print(f"[DEBUG] {index + 1} 件目のデータを処理中: {field}")

                    # 必須フィールドのデフォルト値を設定
                    field.setdefault("id", None)  # IDがない場合、Noneを設定
                    field.setdefault("choices", "")  # choicesがNoneの場合、空文字にする

                    # 必須フィールドのチェック
                    required_keys = ["field_name", "field_type", "schema_id"]
                    if not all(key in field and field[key] is not None for key in required_keys):
                        print(f"[ERROR] 必須フィールドが不足しています: {field}")
                        continue


                    # SchemaFieldの更新または作成
                    field_obj, field_created = SchemaFields.objects.update_or_create(
                        schema_id=field['schema_id'],  # schema_idを指定
                        name=field['field_name'],
                        defaults={
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
        return "インポート完了"

    except Exception as e:
        print("[CRITICAL] インポート処理中に予期せぬエラーが発生しました。")
        traceback.print_exc()
        return "インポート中にエラーが発生しました。"
