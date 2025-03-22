import csv
from django.apps import apps
import logging

logger = logging.getLogger(__name__)

def export_model_fields_to_csv(model_name, file_name):
    """
    指定されたモデルのフィールド情報をCSVにエクスポート
    """
    try:
        # 動的にモデルを取得
        model = apps.get_model("automation", model_name)
        fields = [field.name for field in model._meta.get_fields() if not field.auto_created]

        # フィールド情報をCSVに書き込み
        with open(file_name, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            logger.info(f"Fields exported to {file_name}")
    except LookupError as e:
        logger.error(f"Model '{model_name}' could not be found. Ensure it is registered before calling this function: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during field export: {e}")

# 必要に応じて個別に関数を呼び出す設計に変更する
