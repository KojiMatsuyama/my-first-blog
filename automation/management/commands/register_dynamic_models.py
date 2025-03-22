from django.core.management.base import BaseCommand
from automation.models import register_dynamic_model
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Register dynamic models for the application."

    def handle(self, *args, **kwargs):
        """
        エントリーポイント。動的モデルを順次登録する。
        """
        print("\n========== Starting the dynamic model registration process ==========")

        # 登録対象モデルリスト
        models_to_register = [
            ("Evaluation", "Evaluation", "evaluation"),
            ("Decision", "Decision", "decision"),
            ("Recognition", "Recognition", "recognition"),
        ]
        print(f"[INFO] Models to register: {models_to_register}")

        # モデル登録処理
        for model_name, schema_name, table_name in models_to_register:
            self.register_model(model_name, schema_name, table_name)

        print("\n========== Dynamic model registration process completed ==========")

    def register_model(self, model_name, schema_name, table_name):
        """
        単一の動的モデルを登録する。
        """
        try:
            print(f"\n[TRACE] Attempting to register model: {model_name}")
            print(f"[TRACE] Schema name: {schema_name}, Table name: {table_name}")
            print(f"[TRACE] Calling 'register_dynamic_model' for {model_name}")

            # モデル登録を試行
            register_dynamic_model(model_name, schema_name, table_name)

            # 成功時のメッセージ
            self.stdout.write(self.style.SUCCESS(f"[SUCCESS] Dynamic model '{model_name}' registered successfully."))
            print(f"[TRACE] Model '{model_name}' successfully registered.")
        except Exception as e:
            # エラー処理
            error_message = f"[ERROR] Error registering model '{model_name}': {e}"
            print(error_message)
            logger.error(error_message)
            self.stderr.write(self.style.ERROR(error_message))

