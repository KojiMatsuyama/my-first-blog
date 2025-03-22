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

def evaluate_bitwise_or(target: str, mask: str) -> bool:
    """
    評価対象のテキストと評価ビットを基に論理和を計算し、
    結果が評価ビットと一致する場合はTrue、一致しない場合はFalseを返す。

    Args:
        target (str): 評価対象のテキスト（8文字のビット文字列）
        mask (str): 評価ビット（8文字のビット文字列）

    Returns:
        bool: 論理和の結果が評価ビットと一致するかどうか
    """
    # 入力値の長さチェック
    if len(target) != 8 or len(mask) != 8:
        raise ValueError("Both target and mask must be 8-character binary strings.")

    # 2進数に変換
    target_int = int(target, 2)
    mask_int = int(mask, 2)

    # 論理和を計算
    result = target_int | mask_int

    # 結果を元の形式（文字列）に戻して評価
    return format(result, '08b') == mask
