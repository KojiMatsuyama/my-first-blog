from django.db import models
from django.apps import apps

### スキーマモデル ###
class Schema(models.Model):
    """
    動的フィールドを管理するスキーマモデル
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    # デフォルトのマネージャー
    objects = models.Manager()

    # カスタムマネージャー
    custom_objects = models.Manager()

    @classmethod
    def get(cls, name):
        """
        指定されたスキーマ名を取得する。安全に処理を行うためのメソッド。
        """
        try:
            # `name` の値を確認してデバッグ
            print(f"Looking for schema with name: {name}")

            # nameが文字列であることを確認する
            if not isinstance(name, str):
                raise ValueError("The 'name' parameter must be a string.")

            # スキーマを検索
            schema = cls.objects.get(name=name)
            return schema

        except cls.DoesNotExist:
            # 存在しない場合のハンドリング
            print(f"Schema with name '{name}' does not exist.")
            return None
        except Exception as e:
            # その他のエラーをキャッチ
            print(f"An error occurred: {e}")
            raise

    def __str__(self):
        return self.name

### スキーマに紐づくフィールド ###
class SchemaFields(models.Model):
    """
    スキーマ内のフィールドを定義
    """
    FIELD_TYPES = [
        ('CharField', 'Character Field'),
        ('TextField', 'Text Field'),
        ('IntegerField', 'Integer Field'),
        ('BooleanField', 'Boolean Field'),
        ('ChoiceField', 'Choice Field'),  # 選択式フィールド
    ]

    schema = models.ForeignKey(Schema, on_delete=models.CASCADE, related_name="fields")
    name = models.CharField(max_length=255)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
    is_required = models.BooleanField(default=False)
    choices = models.TextField(blank=True, null=True, help_text="カンマ区切りで選択肢を入力")

    def __str__(self):
        return f"{self.schema.name} - {self.name}"

    def get_choices(self):
        """
        選択式フィールド用の選択肢リストを取得
        """
        if self.choices:
            return [(choice.strip(), choice.strip()) for choice in self.choices.split(",")]
        return None

### スキーマフィールド取得関数 ###
def get_schema_fields(schema_name):
    """
    スキーマに基づいてフィールドを取得
    """
    try:
        # 仕方ないので、いろいろ工夫指定されたアプリ名のモデルにアクセス
        # エラー回避のため仕方なく追加
        # objects = models.Manager()  # デフォルトの objects を追加
        # カスタムマネージャー

        # モデルへの紐付け確認
        print(f"Is 'objects' tied to a model: {hasattr(Schema.objects, 'model')}")

        # 利用可能なスキーマ名を取得
        try:
            available_schemas = Schema.objects.all().values_list("name", flat=True)
            # available_schemas2 = objects.all().values_list("name", flat=True)

            print(f"Available schemas via Schema.objects: {list(available_schemas)}")
            # print(f"Available schemas via Schema.objects: {list(available_schemas2)}")
        except Exception as e:
            print(f"Error with Schema.objects: {e}")

        try:
            available_schemas_with_objects = Schema.objects.all().values_list("name", flat=True)
            print(f"Available schemas via objects: {list(available_schemas_with_objects)}")
        except Exception as e:
            print(f"Error with objects.all(): {e}")

        # schema_name = "Evaluation"
        try:
            # schema = Schema.get(name=schema_name)
            schema = Schema.objects.get(name__iexact=schema_name)
            print(f"Schema found via objects: {schema}")
        except Exception as e:
            print(f"Error with objects.get(): {e}")


        # モデルへの紐付け確認
        print(f"Is 'objects' tied to a model: {hasattr(Schema.objects, 'model')}")

        # 利用可能なスキーマ名を取得
        try:
            available_schemas = Schema.objects.all().values_list("name", flat=True)
            print(f"Available schemas via Schema.objects: {list(available_schemas)}")
        except Exception as e:
            print(f"Error with Schema.objects: {e}")

        try:
            available_schemas_with_objects = Schema.objects.all().values_list("name", flat=True)
            print(f"Available schemas via objects: {list(available_schemas_with_objects)}")
        except Exception as e:
            print(f"Error with objects.all(): {e}")

        schema_name = "Evaluation"
        try:
            schema = Schema.objects.get(name=schema_name)
            print(f"Schema found via objects: {schema}")
        except Exception as e:
            print(f"Error with objects.get(): {e}")

        # objectsの有効性を確認
        if hasattr(Schema, "objects"):
            print("Schema model has a valid objects manager.")
        else:
            print("Schema model does NOT have a valid objects manager.")

        # available_schemas = Schema.objects.all().values_list("name", flat=True)
        available_schemas = Schema.objects.all().values_list("name", flat=True)

        print(f"Available schemas in the database: {list(available_schemas)}")
        # ---------------

        app_label = "automation"
        app_config = apps.get_app_config(app_label)
        registered_models = app_config.get_models()  # モデルオブジェクトを取得
        print(f"Registered models in app '{app_label}': {[model.__name__ for model in registered_models]}")

        # schema_name = "Evaluation"
        schema = Schema.objects.get(name=schema_name)
        # schema = objects.get(name=schema_name)

        fields = schema.fields.all()

        # モデルデバッグ
        if not fields:
            print(f"アプリ '{app_label}' にはモデルが一つも定義されていません。")
        else:
            for field in fields:
                print(f"フィールド名: {field.name}, フィールドタイプ: {field.field_type}")

        # フィールド情報をリスト形式で返す
        return [
            {
                "name": field.name,
                "type": field.field_type,
                "required": field.is_required,
                "choices": field.get_choices() if hasattr(field, "get_choices") else None,  # 安全にchoicesを取得
                "max_length": getattr(field, "max_length", None),  # 文字列型フィールド用
                "decimal_places": getattr(field, "decimal_places", None),  # DecimalField用
                "max_digits": getattr(field, "max_digits", None)  # DecimalField用
            }
            for field in fields
        ]
    except Schema.DoesNotExist:
        return None
    except Exception as e:
        raise ValueError(f"フィールド取得中に予期しないエラーが発生しました: {str(e)}")
