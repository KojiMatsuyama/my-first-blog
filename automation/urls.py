from django.urls import path
from .views import (
    IndexView, DynamicRecognitionView, ImportModelView,
    ExportUnifiedView, export_schema_filtered  # 修正：必要なビューをすべてインポート
)

app_name = 'automation'

# URLパターンをまとめて定義
urlpatterns = [
    # トップページ関連
    path('', IndexView.as_view(), name='index'),
    path('index/', IndexView.as_view(), name='index'),
    path('index.html', IndexView.as_view(), name='index_html'),

    # 動的フォームの生成
    path('recognition/form/<str:schema_name>/', DynamicRecognitionView.as_view(), name='dynamic_form'),

    # データエクスポート
    path('export/unified/<str:schema_name>/', ExportUnifiedView.as_view(), name='export_unified'),
    # path('export/schema/', export_schema_json, name='export_schema_json'),
    path('export-filtered/', export_schema_filtered, name='export_schema_filtered'),  # 修正：インデント調整＆ビュー追加

    # データインポート
    path('import/<str:schema_name>/', ImportModelView.as_view(), name='import_model'),
]

# インポートURLのリダイレクト設定を追加（個別設定を簡素化）
schema_import_urls = {
    'Evaluation': 'import/evaluation/',
    'Decision': 'import/decision/',
    'Recognition': 'import/recognition/',
}

# 動的にインポートURLを追加
for schema_name, url in schema_import_urls.items():
    urlpatterns.append(
        path(url, ImportModelView.as_view(), name=f'import_{schema_name.lower()}', kwargs={'schema_name': schema_name})
    )
