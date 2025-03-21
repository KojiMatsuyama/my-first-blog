from .schema import get_schema_fields
from django.apps import apps
import logging

# ログ設定
logger = logging.getLogger(__name__)

class Decision:
    """
    judgment を基に評価を行い、動的スキーマ 'decision' に基づいて結果を取得するクラス。
    """
    def __init__(self, judge_value):
        """
        初期化
        :param judge_value: 評価から渡された judge の値
        """
        self.judge_value = judge_value
        self.schema_name = "decision"  # 固定スキーマ名
        self.model = apps.get_model('automation', 'Decision')  # 遅延インポートでモデルを取得

    def evaluate(self):
        """
        judge に基づいて decision を評価し、結果を返す
        :return: (評価結果, エラーメッセージ)
        """
        logger.debug(f"[DEBUG] Starting evaluation for judge='{self.judge_value}'")
        print(f"[DEBUG] Starting evaluation for judge='{self.judge_value}'")

        try:
            # judge フィールドで検索
            decision_instance = self.model.objects.filter(judge=self.judge_value).first()

            if not decision_instance:
                error_message = f"judge='{self.judge_value}' に一致する decision データが見つかりません。"
                logger.warning(f"[WARNING] {error_message}")
                print(f"[WARNING] {error_message}")
                return None, error_message

            # 評価結果を辞書形式で構築
            result_data = {
                field.name: getattr(decision_instance, field.name, None)
                for field in self.model._meta.fields
            }
            logger.info("[INFO] Decision evaluation successful.")
            print("[INFO] Decision evaluation successful.")
            logger.debug(f"[DEBUG] Decision result data: {result_data}")
            print(f"[DEBUG] Decision result data: {result_data}")

            return result_data, None

        except Exception as e:
            error_message = f"[ERROR] Exception during Decision evaluation: {e}"
            logger.error(error_message)
            print(error_message)
            return None, error_message
