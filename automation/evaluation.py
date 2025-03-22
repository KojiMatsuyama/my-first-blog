import logging
from .schema import get_schema_fields
from django.apps import apps
from django.core.exceptions import MultipleObjectsReturned

logger = logging.getLogger(__name__)

class Evaluation:
    def __init__(self, input_data):
        self.input_data = input_data
        self.schema_name = "evaluation"
        self.model = apps.get_model('automation', 'evaluation')
        logger.info("Evaluation インスタンスを初期化: input_data=%s", input_data)
        print("[INIT] Evaluation インスタンスを初期化: input_data=", input_data)

    def get_schema_fields(self):
        schema_fields = get_schema_fields(self.schema_name)
        logger.info("取得したスキーマフィールド: %s", schema_fields)
        print("[SCHEMA] 取得したスキーマフィールド:", schema_fields)

        if not schema_fields:
            raise ValueError(f"スキーマ '{self.schema_name}' が見つかりません。")
        return schema_fields

    def validate_model_fields(self, schema_fields):
        missing_fields = [
            field['name'] for field in schema_fields
            if not hasattr(self.model, field['name'])
        ]
        if missing_fields:
            raise AttributeError(f"モデルに存在しないフィールド: {', '.join(missing_fields)}")

        logger.info("モデルのフィールド検証完了: %s", schema_fields)
        print("[VALIDATE] モデルのフィールド検証完了:", schema_fields)

    def build_filter_conditions(self, schema_fields):
        # None ではない値だけをフィルタ条件にする（大文字小文字を区別しない検索に変更）
        filter_conditions = {
            f"{field['name']}__iexact": self.input_data.get(field['name'])
            for field in schema_fields
            if self.input_data.get(field['name']) is not None
        }
        logger.info("構築したフィルタ条件: %s", filter_conditions)
        print("[FILTER] 構築したフィルタ条件:", filter_conditions)
        return filter_conditions

    def evaluate(self):
        try:
            logger.info("入力データ: %s", self.input_data)  # 入力データ全体をログ出力
            print("[EVALUATE] 入力データ:", self.input_data)

            schema_fields = self.get_schema_fields()
            self.validate_model_fields(schema_fields)
            filter_conditions = self.build_filter_conditions(schema_fields)

            try:
                # 条件に一致するデータを取得
                matches = self.model.objects.filter(**filter_conditions)

                logger.info("使用したフィルタ条件: %s", filter_conditions)
                logger.info("マッチしたオブジェクト数: %d", matches.count())

                print("[MATCH] 使用したフィルタ条件:", filter_conditions)
                print("[MATCH] マッチしたオブジェクト数:", matches.count())

                # データベースに存在する全データをログに記録
                all_records = list(self.model.objects.all().values())
                logger.info("データベース内の全レコード数: %d", len(all_records))
                logger.debug("データベース内の全レコード: %s", all_records)

                print("[DB] データベース内の全レコード数:", len(all_records))
                print("[DB] データベース内の全レコード:", all_records)

                if matches.exists():
                    # 条件に一致した場合は「連絡なし」に更新
                    matches.update(judge="連絡なし")
                    judge = matches.first()
                    judge.refresh_from_db()  # DBの最新情報を取得
                    logger.info("マッチしたレコード: %s", judge.__dict__)
                    print("[UPDATE] マッチしたレコード:", judge.__dict__)
                else:
                    # 条件に一致しない場合は「連絡あり」を返す
                    logger.info("データが見つからないため '連絡あり' を設定")
                    logger.info("検索条件: %s", filter_conditions)  # 追加: マッチしなかった条件を明示
                    print("[NO MATCH] データが見つからないため '連絡あり' を設定")
                    print("[NO MATCH] 検索条件:", filter_conditions)
                    judge = {'message': "連絡あり"}

            except MultipleObjectsReturned:
                logger.warning("複数件のデータが一致しました。最初のレコードのみを使用します。")
                print("[WARNING] 複数件のデータが一致しました。最初のレコードのみを使用")
                matches.update(judge="連絡なし")
                judge = matches.first()
                judge.refresh_from_db()

            result_data = {
                field['name']: getattr(judge, field['name'], None)
                for field in schema_fields
            }

            # judge が辞書の場合は特別処理
            if isinstance(judge, dict):
                result_data['judge'] = judge['message']

            logger.info("返却するデータ: %s", result_data)
            logger.info("返却データの要素数: %d", len(result_data))

            print("[RESULT] 返却するデータ:", result_data)
            print("[RESULT] 返却データの要素数:", len(result_data))

            return result_data, None

        except Exception as e:
            logger.exception("評価中に例外が発生: %s", str(e))
            print("[ERROR] 評価中に例外が発生:", str(e))
            return None, str(e)
