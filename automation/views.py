from django.views.generic import TemplateView, FormView
from django.apps import apps
import os
import json
import logging
import traceback
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import models
from django.shortcuts import render
from .excel_to_json import excel_to_json
from django.core.exceptions import ObjectDoesNotExist
from .admin import Schema, SchemaFields
from django.http import HttpResponse, JsonResponse
from django.apps import apps
import json
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render, redirect
# from .models import Schema, SchemaField

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
        elif schema_name == 'Recognition':
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
            _, file_extension = os.path.splitext(uploaded_file.name)

            if file_extension == '.xlsx':
                # エクセルファイルの場合、JSONに変換
                json_file_path = 'output.json'  # 出力先パス
                # excel_to_json(uploaded_file.temporary_file_path(), json_file_path)
                excel_to_json(uploaded_file, json_file_path)  # 変更点

                with open(json_file_path, 'r', encoding='utf-8') as json_file:
                    data = json.load(json_file)  # 変換後のJSONデータを読み込み
            elif file_extension == '.json':
                # JSONファイルの場合、そのまま読み込み
                data = json.load(uploaded_file)
            else:
                logger.error(f"サポートされていないファイル形式です: {file_extension}")
                return JsonResponse({"error": f"サポートされていないファイル形式です: {file_extension}"}, status=400)

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

from .import_schema_from_json import import_schema_from_json

class ImportSchemaView(View):
    def get(self, request, *args, **kwargs):
        # スキーマ選択とファイルアップロード用のフォームを表示
        return render(request, 'import_schema.html')

    def post(self, request, *args, **kwargs):
        schema_name = request.POST.get('schema_name')
        json_file = request.FILES.get('json_file')

        if not schema_name or not json_file:
            return JsonResponse({'error': 'スキーマ名とJSONファイルは必須です。'}, status=400)

        try:
            data = json.load(json_file)

            # スキーマの作成または取得
            schema, created = Schema.objects.get_or_create(name=schema_name)

            # 既存のフィールドを削除して再作成
            SchemaFields.objects.filter(schema=schema).delete()

            for field in data.get('fields', []):
                SchemaFields.objects.create(
                    schema=schema,
                    name=field['name'],
                    field_type=field['field_type'],
                    is_required=field.get('is_required', False)
                )

            return JsonResponse({'success': f'{schema_name} スキーマをインポートしました。'})

        except Exception as e:
            return JsonResponse({'error': f'インポート中にエラーが発生しました: {str(e)}'}, status=500)

# def export_schema_json(request):
#     try:
#         print("export_schema_json に到達")
#         logger.info("export_schema_json に到達")
#
#         # Schema モデルを取得
#         SchemaModel = apps.get_model('automation', 'Schema')
#         schemas = SchemaModel.objects.all()
#         print(f"取得したスキーマ数: {schemas.count()}")
#
#         # SchemaField のリレーション名を確認
#         if hasattr(schemas.first(), 'fields'):
#             print("スキーマに 'fields' リレーションが存在します")
#             schemas = schemas.prefetch_related('fields')
#             field_attr = 'fields'
#         else:
#             print("スキーマに 'schemafield_set' リレーションが存在します")
#             schemas = schemas.prefetch_related('schemafield_set')
#             field_attr = 'schemafield_set'
#
#         # JSONデータを構築
#         schema_list = []
#         for schema in schemas:
#             print(f"スキーマ: {schema.name}, ID: {schema.id}")
#             fields_data = []
#             for field in getattr(schema, field_attr).all():
#                 print(f"  フィールド: {field.name}, ID: {field.id}")
#                 fields_data.append({
#                     "id": field.id,
#                     "name": field.name,
#                     "field_type": field.field_type,
#                     "is_required": field.is_required,
#                     "choices": field.choices,
#                 })
#             schema_list.append({
#                 "id": schema.id,
#                 "name": schema.name,
#                 "description": schema.description,
#                 "fields": fields_data,
#             })
#
#         # JSONデータをダウンロード形式で返す
#         response_data = json.dumps(schema_list, ensure_ascii=False, indent=4)
#         print(f"レスポンスデータ（サンプル）: {response_data[:200]}")  # 最初の200文字だけ表示
#
#         # response = HttpResponse(response_data, content_type='application/json')
#         response = HttpResponse(response_data, content_type='application/octet-stream')
#         response['Content-Disposition'] = 'attachment; filename="schema_export.json"'
#
#         # ✅ キャッシュ防止ヘッダーを追加（必要に応じて）
#         response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#         response['Pragma'] = 'no-cache'
#         response['Expires'] = '0'
#
#         print("レスポンス準備完了")
#         logger.info("[INFO] Content-Disposition: %s", response['Content-Disposition'])
#         logger.info("[INFO] Response Content-Type: %s", response['Content-Type'])
#         logger.info("[INFO] Response Data (Sample): %s", response_data[:500])
#         logger.info("[INFO] Content-Disposition: %s", response['Content-Disposition'])
#
#         return response
#
#     except Exception as e:
#         print(f"エラー発生: {e}")
#         logger.error(f"エラーが発生しました: {e}")
#         return HttpResponse(
#             json.dumps({"error": f"エラーが発生しました: {str(e)}"}, ensure_ascii=False),
#             content_type='application/json',
#             status=500
#         )
#
#     except Exception as e:
#         logger.error(f"export_schema_json エラー: {e}")
#         return JsonResponse({"error": "エクスポート中にエラーが発生しました"}, status=500)


def export_schema_filtered(request):
    """
    指定されたスキーマ名に基づいてデータをエクスポート
    """
    print("export_schema_filtered に到達")  # 到達確認
    schema_name = request.GET.get('schema_name')  # GETパラメータからスキーマ名を取得
    if not schema_name:
        print("スキーマ名が指定されていません")  # 確認用
        return HttpResponse(
            json.dumps({"error": "スキーマ名が指定されていません。"}, ensure_ascii=False),
            content_type='application/json',
            status=400
        )

    try:
        # スキーマデータをフィルタリング
        print(f"指定されたスキーマ名: {schema_name}")  # 確認用
        schema = Schema.objects.filter(name=schema_name).first()
        if not schema:
            print(f"スキーマ '{schema_name}' が見つかりません")  # 確認用
            return HttpResponse(
                json.dumps({"error": f"スキーマ '{schema_name}' が見つかりません。"}, ensure_ascii=False),
                content_type='application/json',
                status=404
            )

        print(f"取得したスキーマ: ID={schema.id}, 名前={schema.name}, 説明={schema.description}")  # 確認用

        # 関連するフィールドデータを取得
        schema_fields = SchemaFields.objects.filter(schema=schema)  # `schema` に修正
        print(f"関連フィールド数: {schema_fields.count()}")  # 確認用

        # 各フィールドのデータを出力
        for field in schema_fields:
            print(
                f"フィールド - ID: {field.id}, 名前: {field.name}, 型: {field.field_type}, 必須: {field.is_required}")  # 確認用

        # データ構築
        schema_data = {
            "schema": {
                "id": schema.id,
                "name": schema.name,
                "description": schema.description
            },
            "fields": [
                {
                    "id": field.id,
                    "field_name": field.name,
                    "field_type": field.field_type,
                    # "field_description": field.field_description
                }
                for field in schema_fields
            ]
        }

        # JSONとしてエクスポート
        response_data = json.dumps(schema_data, ensure_ascii=False, indent=4)
        print(f"エクスポートするデータ（サンプル）: {response_data[:200]}")  # 最初の200文字を出力
        response = HttpResponse(response_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{schema_name}_export.json"'
        print("レスポンスの準備が完了しました")  # 確認用
        return response

    except Exception as e:
        print(f"エラーが発生しました: {e}")  # エラーメッセージを表示
        return HttpResponse(
            json.dumps({"error": f"エラーが発生しました: {str(e)}"}, ensure_ascii=False),
            content_type='application/json',
            status=500
        )

class ExportUnifiedView(View):
    def get(self, request, schema_name, *args, **kwargs):
        try:
            logger.info(f"ExportUnifiedView: {schema_name} を処理中")

            # 動的にモデルを取得
            Model = apps.get_model('automation', schema_name)
            objects = Model.objects.all().values()

            if not objects.exists():
                logger.warning(f"モデル '{schema_name}' にデータが存在しません。ダミーデータを生成します。")
                dummy_data = self.create_dummy_data(Model)
                objects = [dummy_data]

            # JSONデータ作成
            export_data = {
                "schema": self.get_schema_info(schema_name, Model),
                "data": list(objects),
            }

            # JSONレスポンスを返す
            json_data = json.dumps(export_data, ensure_ascii=False, indent=4)
            file_name = f"{schema_name}_export.json"
            response = HttpResponse(json_data, content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response

        except ObjectDoesNotExist:
            logger.error(f"モデル '{schema_name}' が見つかりません。")
            return JsonResponse({"error": f"モデル '{schema_name}' が存在しません。"}, status=404)

        except Exception as e:
            logger.exception(f"ExportUnifiedView エラー: {e}")
            traceback.print_exc()
            return JsonResponse({"error": "エクスポート中にエラーが発生しました"}, status=500)

    def get_schema_info(self, schema_name, Model):
        return {
            "model": schema_name,
            "fields": [
                {
                    "name": field.name,
                    "type": field.get_internal_type(),
                }
                for field in Model._meta.fields
            ],
        }

    def create_dummy_data(self, Model):
        dummy_data = {}
        for field in Model._meta.fields:
            if field.get_internal_type() == 'CharField':
                dummy_data[field.name] = "サンプル"
            elif field.get_internal_type() == 'IntegerField':
                dummy_data[field.name] = 0
            else:
                dummy_data[field.name] = None
        return dummy_data

    def get_schema_info(self, schema_name, model):
        """スキーマと関連するフィールド情報を取得"""
        try:
            SchemaModel = apps.get_model('automation', 'Schema')
            schema = SchemaModel.objects.prefetch_related('fields').get(name=schema_name)
            field_attr = 'fields' if hasattr(schema, 'fields') else 'schemafield_set'

            schema_info = {
                "id": schema.id,
                "name": schema.name,
                "description": schema.description,
                "fields": [
                    {
                        "id": field.id,
                        "name": field.name,
                        "field_type": field.field_type,
                        "is_required": field.is_required,
                        "choices": getattr(field, "choices", None),  # choices属性が存在する場合のみ取得
                        "max_length": getattr(field, "max_length", None),  # 文字列フィールド用
                        "decimal_places": getattr(field, "decimal_places", None),  # DecimalField用
                        "max_digits": getattr(field, "max_digits", None),  # DecimalField用
                        "default_value": getattr(field, "default", None)  # デフォルト値を追加で取得
                    }

                    for field in getattr(schema, field_attr).all()
                ],
            }
            return schema_info

        except Exception as e:
            logger.warning(f"スキーマ情報の取得中にエラーが発生しました: {e}")
            return {"error": "スキーマ情報の取得に失敗しました。"}

    def create_dummy_data(self, model):
        """モデルに基づきダミーデータを生成"""
        dummy_data = {}
        for field in model._meta.get_fields():
            if field.is_relation:
                continue  # リレーションフィールドは除外

            # 各フィールド型に応じたサンプル値を生成
            if isinstance(field, models.AutoField):
                dummy_data[field.name] = 1
            elif isinstance(field, models.IntegerField):
                dummy_data[field.name] = 0
            elif isinstance(field, models.CharField):
                dummy_data[field.name] = f"sample_{field.name}"
            elif isinstance(field, models.BooleanField):
                dummy_data[field.name] = False
            elif isinstance(field, models.DateField):
                dummy_data[field.name] = "2025-01-01"
            elif isinstance(field, models.DateTimeField):
                dummy_data[field.name] = "2025-01-01T00:00:00Z"
            else:
                dummy_data[field.name] = None

        return dummy_data
    def get_dynamic_model(self, schema_name):
        """
        スキーマ名に基づいて動的モデルを取得
        """
        from django.apps import apps
        try:
            # automationアプリの全モデルを取得
            models_in_automation = apps.get_app_config('automation').get_models()

            # デバッグのためモデル一覧を表示
            for model in models_in_automation:
                print(f"Model: {model.__name__}")

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

from .forms import SchemaImportForm

class ImportSchemaSelectedView(View):
    template_name = 'schemas_upload.html'

    def get(self, request, schema_name):
        form = SchemaImportForm()
        return render(request, self.template_name, {'form': form, 'schema_name': schema_name})

    def post(self, request, schema_name):
        form = SchemaImportForm(request.POST, request.FILES)

        if form.is_valid():
            json_file = request.FILES['json_file']

            try:
                # JSONデータの読み込みとインポート実行
                json_data = json_file.read().decode('utf-8')
                import_schema_from_json(json_data)

                return JsonResponse({"success": True, "message": f"{schema_name} のスキーマをインポートしました。"})

            except Exception as e:
                return JsonResponse({"success": False, "message": str(e)})

        return render(request, self.template_name, {'form': form, 'schema_name': schema_name})
