import json
from .schema import Schema  # schema.py から Schema をインポート

def get_schema_fields(schema_name):
    """
    指定されたスキーマ名に基づいて、スキーマのフィールド情報を取得します。

    Args:
        schema_name (str): スキーマ名。

    Returns:
        list[dict]: フィールド情報のリスト（各フィールドは辞書形式）。
                    例: [{"name": ..., "type": ..., "required": ..., "choices": ...}, ...]
        None: 指定したスキーマが存在しない場合。
    """
    try:
        schema = Schema.objects.get(name=schema_name)  # スキーマを取得
        fields = schema.fields.all()  # 関連フィールドを取得
        return [
            {
                "name": field.name,
                "type": field.field_type,
                "required": field.is_required,
                "choices": json.loads(field.choices) if field.choices else None
            }
            for field in fields
        ]
    except Schema.DoesNotExist:
        return None

