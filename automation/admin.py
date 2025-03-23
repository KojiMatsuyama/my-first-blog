from django.contrib import admin
from django import forms
from django.apps import apps
from .schema import Schema, SchemaFields


### SchemaField Inline ###
class SchemaFieldInline(admin.TabularInline):
    """
    Schema に関連付けられた SchemaField をインライン編集可能に
    """
    model = SchemaFields
    extra = 1
    fields = ("name", "field_type", "is_required", "choices")
    verbose_name = "スキーマフィールド"
    verbose_name_plural = "スキーマフィールド"
    help_text = "ChoiceField の場合、choices にカンマ区切りで選択肢を入力してください。"

### Schema 管理画面 ###
@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    """
    Schema モデルの管理画面
    """
    list_display = ("name", "description")
    search_fields = ("name",)
    inlines = [SchemaFieldInline]

### DynamicFieldMixin ###
class DynamicFieldMixin:
    """
    動的フィールドをサポートするMixin
    """
    field_mapping = {
        "CharField": forms.CharField,
        "IntegerField": forms.IntegerField,
        "BooleanField": forms.BooleanField,
        "ChoiceField": forms.ChoiceField,
        "TextField": forms.CharField,
        "DecimalField": forms.DecimalField,  # 小数を扱うフィールド
        "DateField": forms.DateField,  # 日付を扱うフィールド
        "DateTimeField": forms.DateTimeField  # 日時を扱うフィールド
    }

    def add_dynamic_fields(self, form, schema_name):
        """
        スキーマに基づいて動的フィールドをフォームに追加
        """
        schema = Schema.objects.filter(name=schema_name).first()
        if not schema:
            print(f"Schema '{schema_name}' not found. Skipping dynamic field generation.")
            return form

        for field in schema.fields.all():
            field_name = field.name
            field_type = field.field_type
            options = {"required": field.is_required}

            # 特定タイプに応じた追加設定
            if field_type == "ChoiceField" and field.get_choices():
                options["choices"] = field.get_choices()
            elif field_type == "TextField":
                options["widget"] = forms.Textarea

            field_class = self.field_mapping.get(field_type)
            if field_class:
                try:
                    form.base_fields[field_name] = field_class(**options)
                    print(f"Added field: {field_name} ({field_type})")
                except Exception as e:
                    print(f"Error adding field '{field_name}': {e}")
            else:
                print(f"Unsupported field type: {field_type}")

        return form

    def get_form(self, request, obj=None, **kwargs):
        """
        オーバーライドされたフォーム生成処理
        """
        form = super().get_form(request, obj, **kwargs)
        schema_name = getattr(obj, "schema_name", "Evaluation") if obj else "Evaluation"
        return self.add_dynamic_fields(form, schema_name)

### Generic Dynamic Admin for Models ###
class GenericDynamicAdmin(DynamicFieldMixin, admin.ModelAdmin):
    """
    動的に管理画面を構成する汎用クラス
    """
    def get_fields(self, request, obj=None):
        """
        管理画面に表示するフィールドを動的に取得
        """
        default_fields = super().get_fields(request, obj)
        schema_name = getattr(obj, "schema_name", obj.__class__.__name__) if obj else self.model.__name__
        schema = Schema.objects.filter(name=schema_name).first()

        if not schema:
            print(f"Schema '{schema_name}' not found.")
            return default_fields

        dynamic_fields = [field.name for field in schema.fields.all()]
        return list(dict.fromkeys(default_fields + dynamic_fields))


### モデルの動的管理画面登録 ###
# 遅延インポートを使用してモデルを取得
#try:
    #    Evaluation = apps.get_model('automation', 'Evaluation')
    #Recognition = apps.get_model('automation', 'Recognition')
    #Decision = apps.get_model('automation', 'Decision')
#except LookupError as e:
    #    print(f"[ERROR] Model lookup failed: {e}")
    #    Evaluation = None
    #    Recognition = None
#    Decision = None

#if Evaluation:
    #    @admin.register(Evaluation)
        #    class EvaluationAdmin(GenericDynamicAdmin):
#        pass

#if Recognition:
#    @admin.register(Recognition)
#    class RecognitionAdmin(GenericDynamicAdmin):
#        pass

#if Decision:
#    @admin.register(Decision)
#    class DecisionAdmin(GenericDynamicAdmin):
#        pass
