from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db import models, connection
from django.apps import apps
import logging
import sys

logger = logging.getLogger(__name__)

class AutomationConfig(AppConfig):
    """
    Automationアプリケーションの設定
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "automation"

    def ready(self):
        """
        アプリケーション初期化完了時に実行される
        """
        logger.info("Initializing Automation app...")
        print("DEBUG: AutomationConfig.ready() has been called.")  # 標準出力
        self._connect_post_migrate_signal()

        # サーバー起動時に直接モデルを登録
        try:
            self.register_or_update_dynamic_models()
        except Exception as e:
            logger.error(f"Error during server startup dynamic model registration: {e}")

    def _connect_post_migrate_signal(self):
        """
        post_migrateシグナルに動的モデル登録処理を接続
        """
        try:
            post_migrate.connect(self._post_migrate_register, sender=self)
            logger.info("Successfully connected dynamic model registration to post_migrate signal.")
        except Exception as e:
            logger.error(f"Failed to connect post_migrate signal: {e}")

    def _post_migrate_register(self, **kwargs):
        """
        マイグレーション後に動的モデルを登録または既存のテーブルを更新
        """
        try:
            self.register_or_update_dynamic_models()
        except Exception as e:
            logger.error(f"Error during post_migrate dynamic model registration or update: {e}")

    def register_or_update_dynamic_models(self):
        """
        データベースからスキーマを読み込み、動的モデルを登録または更新。
        必要に応じてテーブルを作成。
        """
        from .dynamic_forms import create_dynamic_model
        from .schema import Schema  # スキーマモデルをインポート

        if "makemigrations" in sys.argv:
            logger.info("Skipping dynamic model registration during makemigrations.")
            return

        logger.info("Registering or updating dynamic models from database schemas...")

        try:
            schemas = Schema.objects.all()

            for schema in schemas:
                table_name = schema.name.lower()
                fields = self._generate_fields(schema)

                if self._table_exists(table_name):
                    logger.info(f"Table '{table_name}' exists. Registering model to app_config...")
                    dynamic_model = create_dynamic_model(
                        name=schema.name,
                        fields=fields,
                        app_label=self.name,
                        module=self.name + '.models'
                    )
                    self._register_to_apps(table_name, dynamic_model)
                    logger.info(f"Dynamic model '{schema.name}' successfully registered (table already existed).")
                else:
                    logger.info(f"Table '{table_name}' does not exist. Creating...")
                    self._create_table_for_model(table_name, fields, schema.name)
                    logger.info(f"Table '{table_name}' created and model registered successfully.")

        except Exception as e:
            logger.error(f"Failed to register or update dynamic models: {e}")

    def _table_exists(self, table_name):
        """
        データベース内に指定されたテーブルが存在するか確認
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s);",
                    [table_name]
                )
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error checking existence of table '{table_name}': {e}")
            return False

    def _create_table_for_model(self, table_name, fields, schema_name):
        """
        指定されたテーブル名とフィールド構造でデータベーステーブルを作成
        """
        from .dynamic_forms import create_dynamic_model
        with connection.schema_editor() as schema_editor:
            try:
                logger.info(f"Creating table '{table_name}' with fields: {fields}")
                dynamic_model = create_dynamic_model(
                    name=schema_name,
                    fields=fields,
                    app_label=self.name,
                    module=self.name + '.models'
                )
                schema_editor.create_model(dynamic_model)
                self._register_to_apps(table_name, dynamic_model)
                logger.info(f"Table '{table_name}' and model '{schema_name}' successfully created.")
            except Exception as e:
                logger.error(f"Error while creating table '{table_name}': {e}")

    def _update_table_fields(self, schema, table_name):
        """
        既存テーブルのフィールド情報とスキーマフィールド情報の差分を確認し、必要な変更を加える
        """
        logger.info(f"Updating fields for table '{table_name}' based on schema '{schema.name}'.")

        # 既存テーブルのフィールドを取得
        existing_fields = self._get_existing_table_columns(table_name)
        logger.debug(f"Existing fields in table '{table_name}': {existing_fields}")

        # スキーマからフィールド情報を取得
        schema_fields = schema.fields.all()

        for schema_field in schema_fields:
            field_name = schema_field.name
            field_type = schema_field.field_type

            # フィールドが存在しない場合に追加
            if field_name not in existing_fields:
                logger.info(f"Adding missing field '{field_name}' of type '{field_type}' to table '{table_name}'.")
                self._add_field_to_table(field_name, field_type, table_name)

    def _get_existing_table_columns(self, table_name):
        """
        既存テーブルのフィールドリストを取得
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = %s;",
                    [table_name]
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching columns for table '{table_name}': {e}")
            return []

    def _add_field_to_table(self, field_name, field_type, table_name):
        """
        テーブルにフィールドを追加
        """
        try:
            alter_sql = None

            if field_type == "CharField":
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {field_name} VARCHAR(255);"
            elif field_type == "IntegerField":
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {field_name} INTEGER;"
            elif field_type == "BooleanField":
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {field_name} BOOLEAN;"

            if alter_sql:
                with connection.cursor() as cursor:
                    cursor.execute(alter_sql)
                logger.info(f"Field '{field_name}' added to table '{table_name}'.")
        except Exception as e:
            logger.error(f"Failed to add field '{field_name}' to table '{table_name}': {e}")

    def _generate_fields(self, schema):
        """
        スキーマに基づきモデルフィールドを生成
        """
        fields = {}
        for schema_field in schema.fields.all():
            field_type = schema_field.field_type
            field_options = {"blank": True, "null": True}

            if field_type == "CharField":
                fields[schema_field.name] = models.CharField(max_length=255, **field_options)
            elif field_type == "TextField":
                fields[schema_field.name] = models.TextField(**field_options)
            elif field_type == "IntegerField":
                fields[schema_field.name] = models.IntegerField(**field_options)
            elif field_type == "BooleanField":
                fields[schema_field.name] = models.BooleanField(**field_options)
            elif field_type == "DecimalField":
                fields[schema_field.name] = models.DecimalField(max_digits=10, decimal_places=2, **field_options)
            elif field_type == "DateField":
                fields[schema_field.name] = models.DateField(**field_options)
            elif field_type == "DateTimeField":
                fields[schema_field.name] = models.DateTimeField(**field_options)
            elif field_type == "ChoiceField":
                field_options["choices"] = schema_field.choices  # 必要であればchoicesを追加
                fields[schema_field.name] = models.CharField(max_length=255, **field_options)
            else:
                raise ValueError(f"未知のフィールドタイプ: {field_type}")  # 未対応のフィールドタイプへの対応
        return fields

    def _register_to_apps(self, table_name, dynamic_model):
        """
        アプリケーションに動的モデルを登録
        """
        try:
            app_config = apps.get_app_config(self.name)
            app_config.models[table_name] = dynamic_model
            logger.info(f"Registered dynamic model '{table_name}' to app_config.")
        except Exception as e:
            logger.error(f"Failed to register model '{table_name}' to apps: {e}")

