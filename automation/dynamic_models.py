from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models, connection
from automation.dynamic_forms import create_dynamic_model

class Command(BaseCommand):
    help = "Manually register and create the Evaluation dynamic model"

    def handle(self, *args, **kwargs):
        model_name = "Evaluation"
        fields = self._define_fields()

        self._log_field_info(fields)

        try:
            # 動的モデルの生成と登録、テーブル作成
            dynamic_model = self._create_and_register_model(model_name, fields)
            self._create_table(dynamic_model, model_name)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error during processing: {e}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Dynamic model '{model_name}' created and registered successfully."))

    def _define_fields(self):
        """
        モデルのフィールドを定義する
        """
        return {
            "judge": {"type": "TextField"},
            "alert": {"type": "TextField"},
            "week": {"type": "TextField"},
            "retail": {"type": "TextField"},
            "wholesale": {"type": "TextField"},
        }

    def _log_field_info(self, fields):
        """
        フィールド情報をログに出力
        """
        print("[INFO] Registering fields for the model:")
        for field_name, field_info in fields.items():
            field_type = field_info["type"]
            print(f"  - Field Name: '{field_name}', Type: '{field_type}'")

    def _create_and_register_model(self, model_name, fields):
        """
        動的モデルを生成し、アプリに登録
        """
        processed_fields = self._process_fields(fields)
        dynamic_model = create_dynamic_model(
            name=model_name,
            fields=processed_fields,
            app_label="automation",
            module="automation.models"
        )
        self._register_model_to_app(dynamic_model, model_name)
        return dynamic_model

    def _process_fields(self, fields):
        """
        フィールド情報をDjangoモデルのフィールドへ変換
        """
        field_map = {
            "TextField": lambda: models.TextField(blank=True, null=True),
            "CharField": lambda: models.CharField(max_length=255, blank=True, null=True),
            "IntegerField": lambda: models.IntegerField(blank=True, null=True),
        }

        processed_fields = {}
        for field_name, field_info in fields.items():
            field_type = field_info["type"]
            processed_fields[field_name] = field_map.get(field_type, lambda: models.TextField(blank=True, null=True))()
            if field_type not in field_map:
                print(f"[WARNING] Unsupported field type '{field_type}'. Defaulting to TextField.")
        return processed_fields

    def _register_model_to_app(self, dynamic_model, model_name):
        """
        アプリケーションにモデルを登録
        """
        app_config = apps.get_app_config("automation")
        app_config.models[model_name.lower()] = dynamic_model
        print(f"[SUCCESS] Dynamic model '{model_name}' registered to app_config.")

    def _create_table(self, dynamic_model, model_name):
        """
        データベースにテーブルを作成
        """
        try:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(dynamic_model)
                print(f"[SUCCESS] Table for dynamic model '{model_name}' created successfully in database.")
        except Exception as e:
            print(f"[ERROR] Failed to create table for model '{model_name}': {e}")
