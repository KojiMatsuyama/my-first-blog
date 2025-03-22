from django.views.generic import TemplateView, FormView
from django.apps import apps
import json
import logging
from django.http import JsonResponse, HttpResponse, Http404
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import models
from django.shortcuts import render

# ログの設定
logger = logging.getLogger(__name__)

class IndexView(TemplateView):
    """トップページのビュー"""
    template_name = 'index.html'

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        """
        POSTリクエストでCSVエクスポートをトリガー
        """
        try:
            model_name = "Evaluation"  # CSVエクスポート対象モデル
            file_name = "evaluation_fields.csv"
            logger.info(f"Starting export for model '{model_name}' to file '{file_name}'.")

            # CSVエクスポート処理を呼び出し
            from .management.commands.export_evaluation_fields_csv import export_model_fields_to_csv
            export_model_fields_to_csv(model_name, file_name)

            logger.info(f"Export completed successfully for model '{model_name}'.")
            return HttpResponse(f"CSV file '{file_name}' has been exported successfully!")
        except Exception as e:
            logger.error(f"Error during CSV export: {e}")
            return HttpResponse(f"Failed to export CSV: {e}", status=500)

class BaseDynamicModelView(TemplateView):
    """動的モデルに関する共通機能を提供する基底ビュー"""

    def get_dynamic_model(self, schema_name):
        """
        スキーマ名に基づいて動的モデルを取得
        """
        try:
            DynamicModel = apps.get_model('automation', schema_name)
            if not DynamicModel:
                raise LookupError(f"モデル '{schema_name}' が見つかりません。")
            return DynamicModel
        except LookupError as e:
            logger.error(str(e))
            raise Http404(f"モデル '{schema_name}' が見つかりません。")

    def validate_json_file(self, uploaded_file):
        """
        アップロードされたファイルがJSON形式であることを検証
        """
        if uploaded_file.content_type != 'application/json':
            raise ValueError("アップロードされたファイルはJSON形式ではありません。")

        try:
            data = json.load(uploaded_file)
            logger.info(f"アップロードされたデータ: {data}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSONのデコードに失敗しました: {e}")
            raise ValueError("JSONの形式が不正です。")

class ImportModelView(BaseDynamicModelView):
    """JSONファイルを動的モデルにインポートするビュー"""

    def get_template_names(self):
        """
        スキーマ名に応じてテンプレートを切り替える
        """
        schema_name = self.kwargs.get('schema_name')
        if schema_name == 'Evaluation':
            return ['evaluation_upload.html']
        elif schema_name == 'Decision':
            return ['decision_upload.html']
        elif schema_name == 'Recognition':  # Recognition用の処理を追加
            return ['recognition_upload.html']
        else:
            raise Http404(f"テンプレートが見つかりません: schema_name='{schema_name}'")


    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        """
        POSTリクエストを処理し、JSONデータをインポート（リスト形式および単一オブジェクト形式に対応）
        """
        schema_name = kwargs.get('schema_name')  # スキーマ名を取得
        logger.info(f"インポート処理を開始します。スキーマ名: {schema_name}")

        try:
            # ファイルがアップロードされているかを確認
            if 'file' not in request.FILES:
                logger.error("ファイルがアップロードされていません。")
                return JsonResponse({"error": "ファイルがアップロードされていません。"}, status=400)

            uploaded_file = request.FILES['file']
            data = self.validate_json_file(uploaded_file)

            # 動的モデルを取得
            DynamicModel = self.get_dynamic_model(schema_name)
            logger.info(f"モデル '{schema_name}' を正常に取得しました。")

            # データ形式を判定して処理
            if isinstance(data, list):
                logger.info(f"データ形式: リスト（件数: {len(data)}）")
                self._import_records(DynamicModel, data)  # リスト形式データを一括処理
            elif isinstance(data, dict):
                logger.info("データ形式: オブジェクト（単一）")
                self._import_record(DynamicModel, data)  # 単一データを処理
            else:
                logger.error("JSON形式が無効です。リストまたはオブジェクトを期待します。")
                return JsonResponse({"error": "無効なJSON形式です。リストまたはオブジェクトでアップロードしてください。"}, status=400)

            return JsonResponse({"message": f"データを'{schema_name}'にインポートしました！"}, status=200)

        except ValueError as e:
            logger.error(f"Validation Error: {e}")
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"インポート処理中にエラーが発生しました: {e}")
            return JsonResponse({"error": f"エラーが発生しました: {str(e)}"}, status=500)

    def _import_record(self, DynamicModel, record):
        """
        個々のレコードをデータベースにインポート
        """
        try:
            # 単一レコードをモデルに登録
            DynamicModel.objects.create(**record)
            logger.info(f"データを登録しました: {record}")
        except Exception as e:
            logger.error(f"データ登録中にエラーが発生しました: {e}")
            raise ValueError(f"登録失敗: {e}")

    def _import_records(self, DynamicModel, records):
        """
        複数のレコードを一括でデータベースにインポート
        """
        for record in records:
            try:
                self._import_record(DynamicModel, record)
            except ValueError as e:
                logger.error(f"レコードのインポート中にエラーが発生しました: {e}")
                raise  # エラーを再スローし、適切に処理

class ExportModelView(BaseDynamicModelView):
    """動的モデルのJSONエクスポートビュー"""

    @method_decorator(csrf_exempt)
    def get(self, request, *args, **kwargs):
        schema_name = kwargs.get('schema_name')
        logger.info(f"エクスポート処理を開始します。スキーマ名: {schema_name}")

        try:
            # 動的モデルを取得
            DynamicModel = self.get_dynamic_model(schema_name)
            logger.info(f"モデル '{schema_name}' を正常に取得しました。")

            # モデルからデータを取得
            data = list(DynamicModel.objects.values())
            logger.info(f"モデル '{schema_name}' からデータを取得しました。件数: {len(data)}")

            if not data:
                # ダミーデータを生成
                logger.warning(f"モデル '{schema_name}' にデータが存在しません。ダミーデータを生成します。")
                fields = DynamicModel._meta.get_fields()
                dummy_data = {}

                for field in fields:
                    if field.is_relation:
                        continue  # リレーションフィールドを除外

                    # フィールド型ごとに適切な値を設定
                    if isinstance(field, models.AutoField):  # IDフィールド
                        dummy_data[field.name] = 1
                    elif isinstance(field, models.IntegerField):  # 整数型
                        dummy_data[field.name] = 0
                    elif isinstance(field, models.CharField):  # 文字列型
                        dummy_data[field.name] = f"sample_{field.name}"
                    elif isinstance(field, models.BooleanField):  # 真偽値型
                        dummy_data[field.name] = False
                    elif isinstance(field, models.DateField):  # 日付型
                        dummy_data[field.name] = "2025-01-01"
                    elif isinstance(field, models.DateTimeField):  # 日時型
                        dummy_data[field.name] = "2025-01-01T00:00:00Z"
                    else:
                        dummy_data[field.name] = None  # その他の型

                data.append(dummy_data)
                logger.info(f"ダミーデータ生成完了: {dummy_data}")

            # データをJSON形式に変換
            json_data = json.dumps(data, ensure_ascii=False, indent=4)
            logger.info(f"データをJSON形式に変換しました。")

            # ファイル名を生成
            file_name = f"{schema_name}_export.json"
            response = HttpResponse(json_data, content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response

        except Http404 as e:
            logger.error(f"モデル '{schema_name}' が見つかりません: {e}")
            return JsonResponse({"error": str(e)}, status=404)
        except Exception as e:
            logger.exception(f"エクスポート処理中に予期しないエラーが発生しました: {e}")
            return JsonResponse({"error": f"エラー: {str(e)}"}, status=500)

    def get_dynamic_model(self, schema_name):
        """
        スキーマ名に基づいて動的モデルを取得
        """
        from django.apps import apps
        try:
            DynamicModel = apps.get_model('automation', schema_name)
            if not DynamicModel:
                raise LookupError(f"モデル '{schema_name}' が見つかりません。")
            return DynamicModel
        except LookupError as e:
            logger.error(f"モデル '{schema_name}' の取得中にエラーが発生しました: {e}")
            raise Http404(f"モデル '{schema_name}' が見つかりません。")

class DynamicRecognitionView(FormView):
    """Recognitionモデル用の動的フォームビュー"""
    template_name = 'recognition.html'

    def get_form_class(self):
        """
        動的スキーマに基づいてフォームを生成
        """
        schema_name = 'Recognition'
        try:
            from .dynamic_forms import generate_dynamic_form
            DynamicForm = generate_dynamic_form(schema_name)
            if not DynamicForm:
                logger.error(f"スキーマ '{schema_name}' のフォームが生成できません。")
                raise Http404(f"スキーマ '{schema_name}' が見つかりません。")
            return DynamicForm

        except Exception as e:
            logger.error(f"フォーム生成中にエラーが発生しました: {e}")
            raise

    def form_valid(self, form):
        """フォームが有効な場合の処理"""
        cleaned_data = form.cleaned_data
        logger.debug(f"[DEBUG] Cleaned data from form: {cleaned_data}")

        try:
            # 評価
            from .evaluation import Evaluation
            logger.info("[INFO] Starting Evaluation process.")

            evaluation_instance = Evaluation(cleaned_data)
            evaluation_result, evaluation_error = evaluation_instance.evaluate()

            logger.debug(f"[DEBUG] Evaluation result: {evaluation_result}, Error: {evaluation_error}")

            if evaluation_error:
                return self._render_error(form, evaluation_error)

            judge_value = evaluation_result.get('judge')
            if not judge_value:
                return self._render_error(form, "評価結果にjudgeフィールドが見つかりません。")

            # 決定
            from .decision import Decision
            decision_instance = Decision(judge_value)
            decision_data, decision_error = decision_instance.evaluate()

            logger.debug(f"[DEBUG] Decision result: {decision_data}, Error: {decision_error}")
            # デバッグポイント: decision_dataの構造を確認
            logger.debug(f"[DEBUG] Decision data structure: {decision_data.keys()}")
            print(f"[DEBUG] Decision data structure: {decision_data.keys()}")  # コンソールでも確認したい場合

            if decision_error:
                return self._render_error(form, decision_error)

            # 正しいテンプレートに渡してレンダリング
            if judge_value == "連絡あり":
                template_name = 'workinstruction_contact.html'
            elif judge_value == "連絡なし":
                template_name = 'workinstruction_no_contact.html'
            else:
                return self._render_error(form, "無効なjudge値です。")

            logger.info(f"[INFO] Rendering result to {template_name}.")
            logger.debug(
                f"[DEBUG] Rendering template: {template_name} with context: {{'form': form, 'result': decision_data, 'error_message': None}}"
            )

            context = {
                'form': form,
                'result': decision_data,
                'error_message': None
            }
            return render(self.request, template_name, context)

        except Exception as e:
            logger.error(f"[ERROR] Exception during form processing: {e}")
            return self._render_error(form, str(e))

    def form_invalid(self, form):
        """フォームが無効な場合の処理"""
        return self.render_to_response({'form': form, 'form_errors': form.errors})

    def _render_error(self, form, error_message):
        logger.error(f"エラー: {error_message}")
        return self.render_to_response({'form': form, 'error_message': error_message})
