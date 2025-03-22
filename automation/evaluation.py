from .schema import get_schema_fields
from django.apps import apps


class Evaluation:
    """
    動的スキーマ 'evaluation' に基づいてデータを評価するクラス
    """
    def __init__(self, input_data):
        """
        初期化
        :param input_data: 入力データ（フォームまたはオブジェクト）
        """
        self.input_data = input_data
        self.schema_name = "evaluation"  # 固定スキーマ名
        self.model = apps.get_model('automation', 'evaluation')  # 遅延インポート

    def get_schema_fields(self):
        """
        スキーマからフィールド情報を取得
        :return: フィールド情報リスト
        """
        schema_fields = get_schema_fields(self.schema_name)
        if not schema_fields:
            raise ValueError(f"スキーマ '{self.schema_name}' が見つかりません。")
        return schema_fields

    def validate_model_fields(self, schema_fields):
        """
        モデルに必要なフィールドが存在するかを検証
        :param schema_fields: スキーマのフィールド情報
        """
        missing_fields = [
            field['name'] for field in schema_fields
            if not hasattr(self.model, field['name'])
        ]
        if missing_fields:
            raise AttributeError(f"モデルに存在しないフィールド: {', '.join(missing_fields)}")

    def build_filter_conditions(self, schema_fields):
        """
        入力データに基づいてフィルタ条件を構築
        :param schema_fields: スキーマのフィールド情報
        :return: フィルタ条件の辞書
        """
        filter_conditions = {
            field['name']: getattr(self.input_data, field['name'], None)
            for field in schema_fields
            if hasattr(self.input_data, field['name'])
        }
        return filter_conditions

    def evaluate(self):
        """
        入力データを評価し、結果を返す
        :return: (評価結果, エラーメッセージ)
        """
        try:
            # スキーマフィールドを取得
            schema_fields = self.get_schema_fields()

            # モデルフィールドの検証
            self.validate_model_fields(schema_fields)

            # フィルタ条件を構築
            filter_conditions = self.build_filter_conditions(schema_fields)

            # データベース内の評価基準と一致するものを取得
            judge = self.model.objects.get(**filter_conditions)

            # 結果を辞書形式で構築
            result_data = {
                field['name']: getattr(judge, field['name'], None)
                for field in schema_fields
            }
            return result_data, None

        except self.model.DoesNotExist:
            return None, "条件に一致するデータが見つかりません。"

        except AttributeError as ae:
            return None, f"モデルフィールドのエラー: {str(ae)}"

        except Exception as e:
            return None, f"予期しないエラーが発生しました: {str(e)}"
