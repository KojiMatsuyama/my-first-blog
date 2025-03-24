from django.urls import path
from .views import (
    IndexView, DynamicRecognitionView, ImportModelView,
    ExportUnifiedView, export_schema_filtered, ImportSchemaView,
    ImportSchemaSelectedView # Schemaインポートビューを追加
)

app_name = 'automation'

# URLパターンをまとめて定義
urlpatterns = [
    # トップページ関連
    path('', IndexView.as_view(), name='index'),
    path('index/', IndexView.as_view(), name='index'),
    path('index.html', IndexView.as_view(), name='index'),

    # 動的フォームの生成
    path('recognition/form/<str:schema_name>/', DynamicRecognitionView.as_view(), name='dynamic_form'),

    # データエクスポート
    path('export/unified/<str:schema_name>/', ExportUnifiedView.as_view(), name='export_unified'),
    path('export-filtered/', export_schema_filtered, name='export_schema_filtered'),

    # データインポート
    # path('import/<str:schema_name>/', ImportModelView.as_view(), name='import_model'),

    # Schemaインポート用URLを追加
    # path('import/schema/', ImportSchemaView.as_view(), name='import_schema'),

    # スキーマ選択インポート
    path('import-filtered/<str:schema_name>/', ImportSchemaSelectedView.as_view(), name='import_schema_selected'),
    # path('import-filtered/', ImportSchemaSelectedView.as_view(), name='import_schema_selected'),
]

# スキーマ用URLのリダイレクト設定を追加（個別設定を簡素化）
schema_urls = {
    'Evaluation': 'evaluation/',
    'Decision': 'decision/',
    'Recognition': 'recognition/',
}

# 動的にインポートURLを追加
for schema_name, url in schema_urls.items():
    urlpatterns.append(
        path(f'import/{url}', ImportModelView.as_view(), name=f'import_{schema_name.lower()}', kwargs={'schema_name': schema_name})
    )

# 動的にエクスポートURLを追加
for schema_name, url in schema_urls.items():
    urlpatterns.append(
        path(f'export/{url}', ExportUnifiedView.as_view(), name=f'export_{schema_name.lower()}', kwargs={'schema_name': schema_name})
    )

