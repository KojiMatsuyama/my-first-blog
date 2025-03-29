from django.db import models
from django import forms
from django.apps import apps


def create_dynamic_model(name, fields=None, app_label="automation", module="automation.models"):
    """
    動的にDjangoモデルを生成する関数
    :param name: モデル名
    :param fields: モデルのフィールド定義（辞書形式）
    :param app_label: アプリケーション名
    :param module: モジュール名
    :return: 生成されたモデルクラス
    """
    print(f"[TRACE] Initializing dynamic model creation for '{name}' with app_label '{app_label}'")
    fields = fields or {}

    # 外部でMetaクラスを生成
    Meta = type("Meta", (), {"app_label": app_label, "db_table": name.lower()})
    fields["Meta"] = Meta  # 動的に生成したMetaクラスを挿入
    fields["__module__"] = module  # モジュール情報を追加

    try:
        dynamic_model = type(name, (models.Model,), fields)
        print(f"[TRACE] Dynamic model '{name}' created successfully with app_label '{app_label}'.")
        return dynamic_model
    except Exception as e:
        raise ValueError(f"[ERROR] Error creating dynamic model '{name}': {e}")


def register_dynamic_model(model_name, schema_name, table_name):
    """
    動的モデルを登録し、アプリケーションに追加する。
    :param model_name: 登録するモデル名
    :param schema_name: スキーマ名（フィールド情報を取得する元）
    :param table_name: テーブル名
    """
    print(f"[TRACE] Registering dynamic model '{model_name}' with schema '{schema_name}' and table '{table_name}'")

    # スキーマを取得
    try:
        from .schema import Schema  # スキーマモジュールのインポート
        schema = Schema.objects.get(name=schema_name)
        schema_fields = schema.fields.all()
        print(f"[INFO] Retrieved schema fields for '{schema_name}': {[field.name for field in schema_fields]}")
    except Schema.DoesNotExist:
        print(f"[ERROR] Schema '{schema_name}' does not exist.")
        return

    # モデルのフィールドを生成
    fields = {}
    for field in schema_fields:
        field_type = field.field_type
        field_kwargs = {"blank": True, "null": True}  # デフォルト設定

        if field_type == "CharField":
            fields[field.name] = models.CharField(max_length=255, **field_kwargs)
        elif field_type == "IntegerField":
            fields[field.name] = models.IntegerField(**field_kwargs)
        elif field_type == "BooleanField":
            fields[field.name] = models.BooleanField(**field_kwargs)
        else:
            print(f"[WARNING] Unsupported field type '{field_type}'. Defaulting to TextField.")
            fields[field.name] = models.TextField(**field_kwargs)

        print(f"[TRACE] Added field '{field.name}' with type '{field_type}'.")

        # 🔴 schema_id を追加
        fields["schema_id"] = models.ForeignKey(Schema, on_delete=models.CASCADE)


    # 動的モデルを作成
    try:
        dynamic_model = create_dynamic_model(model_name, fields, app_label="automation")
        print(f"[TRACE] Model '{model_name}' successfully created.")
    except ValueError as e:
        print(f"[ERROR] Failed to create model '{model_name}': {e}")
        return

    # アプリケーションに登録
    try:
        app_config = apps.get_app_config("automation")
        app_config.models[model_name.lower()] = dynamic_model
        print(f"[SUCCESS] Model '{model_name}' registered successfully in app_config.")
    except Exception as e:
        print(f"[ERROR] Failed to register model '{model_name}' in app_config: {e}")


def generate_dynamic_form(schema_name):
    """
    指定されたスキーマ名に基づいて動的フォームを生成する。
    """
    print(f"[TRACE] Generating dynamic form for schema: {schema_name}")
    try:
        from .schema import Schema  # 必要なスキーマモデルをインポート
        schema = Schema.objects.get(name=schema_name)
        fields = schema.fields.all()

        class DynamicForm(forms.Form):
            pass

        for field in fields:
            field_kwargs = {
                "label": field.name,
                "required": field.is_required,
            }
            if field.field_type == "CharField":
                form_field = forms.CharField(**field_kwargs)
            elif field.field_type == "IntegerField":
                form_field = forms.IntegerField(**field_kwargs)
            elif field.field_type == "BooleanField":
                form_field = forms.BooleanField(**field_kwargs)
            else:
                # 未対応のフィールド型に対するデフォルト処理
                form_field = forms.CharField(**field_kwargs)

            # フィールドをDynamicFormに追加
            DynamicForm.base_fields[field.name] = form_field

        print(f"[SUCCESS] Dynamic form for schema '{schema_name}' generated successfully.")
        return DynamicForm

    except Schema.DoesNotExist:
        print(f"[ERROR] Schema '{schema_name}' does not exist.")
        return None
