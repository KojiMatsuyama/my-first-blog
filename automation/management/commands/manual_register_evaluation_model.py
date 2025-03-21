from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models, connection, transaction
from automation.dynamic_forms import create_dynamic_model


class Command(BaseCommand):
    help = "Manually register and create or update the Evaluation dynamic model"

    def handle(self, *args, **kwargs):
        model_name = "Evaluation"
        fields = {
            "judge": {"type": "TextField"},
            "alert": {"type": "TextField"},
            "week": {"type": "TextField"},
            "retail": {"type": "TextField"},
            "wholesale": {"type": "TextField"},
        }

        self._log_field_info(fields)

        try:
            with transaction.atomic():  # トランザクションでエラーハンドリングを強化
                dynamic_model = self._create_and_register_model(model_name, fields)
                self._create_or_update_table(dynamic_model, model_name, fields)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error during processing: {e}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Dynamic model '{model_name}' created or updated successfully."))

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
        print(f"[TRACE] Processed fields: {processed_fields}")
        return processed_fields

    def _register_model_to_app(self, dynamic_model, model_name):
        """
        アプリケーションにモデルを登録
        """
        app_config = apps.get_app_config("automation")
        app_config.models[model_name.lower()] = dynamic_model
        print(f"[SUCCESS] Dynamic model '{model_name}' registered to app_config.")

    def _create_or_update_table(self, dynamic_model, model_name, fields):
        """
        データベースのテーブルを作成または更新
        """
        try:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(dynamic_model)
                print(f"[SUCCESS] Table for model '{model_name}' created successfully in database.")
        except Exception:
            print(f"[INFO] Table already exists for model '{model_name}'. Attempting to update columns...")
            self._update_table(dynamic_model, model_name, fields)

    def _update_table(self, dynamic_model, model_name, fields):
        """
        既存のテーブルに新しいカラムを追加
        """
        existing_columns = self._get_existing_columns(model_name)
        print(f"[TRACE] Existing columns in table '{model_name}': {existing_columns}")
        with connection.schema_editor() as schema_editor:
            for field_name, field_info in fields.items():
                if field_name not in existing_columns:
                    field_type = dynamic_model._meta.get_field(field_name)
                    print(f"[TRACE] Adding column '{field_name}' of type '{field_type}' to table '{model_name}'...")
                    schema_editor.add_field(dynamic_model, field_type)
                    print(f"[SUCCESS] Added column '{field_name}' to table '{model_name}'.")

    def _get_existing_columns(self, model_name):
        """
        既存のテーブルのカラム名を取得
        """
        with connection.cursor() as cursor:
            query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{model_name.lower()}';"
            print(f"[TRACE] Executing query to fetch existing columns: {query}")
            cursor.execute(query)
            columns = [row[0] for row in cursor.fetchall()]
            print(f"[TRACE] Columns retrieved: {columns}")
            return columns
