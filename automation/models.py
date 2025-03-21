from django.db import models
from automation.dynamic_models import create_dynamic_model
from django.apps import apps
from .utils import get_schema_fields

class DynamicModelBase(models.Model):
    """
    動的モデルの抽象基底クラス
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

def build_dynamic_model(model_name, schema_name, db_table_name):
    """
    動的モデルを作成する共通ロジック
    """
    print(f"[TRACE] Building dynamic model: {model_name}")
    print(f"[TRACE] Schema name: {schema_name}, Table name: {db_table_name}")

    try:
        # スキーマフィールドを取得
        fields = get_schema_fields(schema_name)
        if not fields:
            raise ValueError(f"Schema '{schema_name}' not found or empty.")
        print(f"[TRACE] Retrieved fields for schema '{schema_name}': {fields}")

        # メタ情報を定義
        meta_attributes = {
            "db_table": db_table_name,
            "app_label": "automation"  # 明示的にapp_labelを指定
        }
        meta_class = type("Meta", (), meta_attributes)

        # フィールドを格納する辞書を作成
        dynamic_model_attrs = {
            "Meta": meta_class,
            "__module__": "automation.models",  # モジュール名を明示
        }

        # フィールドを動的に追加
        for field in fields:
            field_name = field["name"]
            field_type = field["type"]
            field_options = {
                "blank": not field.get("required", True),
                "null": not field.get("required", True),
            }

            # フィールドタイプごとの処理
            if field_type == "CharField":
                dynamic_model_attrs[field_name] = models.CharField(
                    max_length=field.get("max_length", 255), **field_options
                )
            elif field_type == "TextField":
                dynamic_model_attrs[field_name] = models.TextField(**field_options)
            elif field_type == "IntegerField":
                dynamic_model_attrs[field_name] = models.IntegerField(**field_options)
            elif field_type == "BooleanField":
                dynamic_model_attrs[field_name] = models.BooleanField(**field_options)
            elif field_type == "ChoiceField" and field.get("choices"):
                choices = [(choice, choice) for choice in field["choices"]]
                dynamic_model_attrs[field_name] = models.CharField(
                    max_length=field.get("max_length", 255),
                    choices=choices,
                    **field_options,
                )
            else:
                raise ValueError(f"Unknown field type '{field_type}' in schema '{schema_name}'.")

            print(f"[TRACE] Added field '{field_name}' of type '{field_type}'")

        # モデルを生成
        dynamic_model = create_dynamic_model(model_name, dynamic_model_attrs)
        print(f"[TRACE] Dynamic model '{model_name}' creation completed.")
        return dynamic_model

    except Exception as e:
        print(f"[ERROR] Error during model creation for '{model_name}': {str(e)}")
        raise e

def register_dynamic_model(model_name, schema_name, db_table_name):
    """
    動的モデルをDjangoアプリケーションに登録する
    """
    print("[*DEBUG] register_dynamic_models called")
    print(f"[TRACE] Registering dynamic model: {model_name}")
    print(f"[TRACE] Schema name: {schema_name}, Table name: {db_table_name}")

    try:
        # モデルを構築
        dynamic_model = build_dynamic_model(model_name, schema_name, db_table_name)
        print(f"[TRACE] Model '{model_name}' built successfully.")

        # モデルをアプリケーションに登録
        app_config = apps.get_app_config("automation")
        print(f"[*DEBUG] Models after registration: {app_config.models}")
        app_config.models[model_name.lower()] = dynamic_model  # 必ず小文字で登録
        print(f"[※TRACE] Model '{model_name}' registered successfully in app config.")
        print(f"[*DEBUG] Registered model name: {model_name.lower()}")


    except Exception as e:
        print(f"[※ERROR] Error during model registration for '{model_name}': {str(e)}")
        raise e
