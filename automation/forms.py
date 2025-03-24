from django import forms
from .schema import get_schema_fields

class DynamicRecognitionForm(forms.Form):
    """
    外部スキーマから動的にフィールドを構築するフォーム
    """

    def __init__(self, schema_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_fields_from_schema(schema_name)

    def add_fields_from_schema(self, schema_name):
        """
        スキーマ名を基にフィールドを動的に追加
        """
        try:
            fields = get_schema_fields(schema_name)
            print(f"Fields fetched for schema '{schema_name}': {fields}")
            if not fields:
                raise ValueError(f"スキーマ '{schema_name}' に有効なフィールドが存在しません。")
        except Exception as e:
            print(f"Error fetching schema fields for '{schema_name}': {e}")
            raise ValueError(f"スキーマ '{schema_name}' のフィールド取得に失敗しました。")

        for field in fields:
            try:
                self.add_field(field)
            except Exception as e:
                print(f"Error adding field '{field.get('name', 'Unknown')}': {e}")

    def add_field(self, field):
        """
        単一フィールドをフォームに追加
        """
        field_type = field.get("type")
        field_name = field.get("name")

        if not field_type or not field_name:
            raise ValueError(f"フィールドのタイプまたは名前が指定されていません: {field}.")

        field_options = {
            "required": field.get("required", False),
            "label": field_name,
            "help_text": field.get("help_text", ""),
            "initial": field.get("initial", None),
        }

        field_mapping = {
            "CharField": lambda: forms.CharField(max_length=255, **field_options),
            "TextField": lambda: forms.CharField(widget=forms.Textarea, **field_options),
            "ChoiceField": lambda: self.create_choice_field(field, field_options),
            "IntegerField": lambda: forms.IntegerField(**field_options),
            "BooleanField": lambda: forms.BooleanField(**field_options),
        }

        field_class_creator = field_mapping.get(field_type)
        if field_class_creator:
            try:
                self.fields[field_name] = field_class_creator()
                print(f"Successfully added field '{field_name}' ({field_type})")
            except Exception as e:
                raise ValueError(f"フィールド '{field_name}' の追加に失敗しました: {e}")
        else:
            print(f"Unsupported field type '{field_type}'. Skipping field '{field_name}'.")

    def create_choice_field(self, field, options):
        """
        ChoiceFieldを作成するヘルパー
        """
        choices = field.get("choices", [])
        if not choices:
            raise ValueError(f"ChoiceField '{field.get('name', 'Unknown')}' に選択肢が指定されていません。")
        return forms.ChoiceField(choices=[(choice, choice) for choice in choices], **options)

    def clean(self):
        """
        動的フィールドのクリーンアップ処理
        """
        cleaned_data = super().clean()
        for field_name in self.fields.keys():
            if field_name not in cleaned_data:
                cleaned_data[field_name] = None
        return cleaned_data

class SchemaImportForm(forms.Form):
    json_file = forms.FileField(label="JSONファイルを選択")