from django.urls import path
from .views import (
    IndexView,
    DynamicRecognitionView,
    ExportModelView,
    ImportModelView,
)

app_name = 'automation'

urlpatterns = [
    # トップページ
    path('', IndexView.as_view(), name='index'),

    # 動的フォームの生成
    path('recognition/form/<str:schema_name>/', DynamicRecognitionView.as_view(), name='dynamic_form'),

    # データエクスポート
    path('export/evaluation/', ExportModelView.as_view(), name='export_evaluation', kwargs={'schema_name': 'Evaluation'}),
    path('export/decision/', ExportModelView.as_view(), name='export_decision', kwargs={'schema_name': 'Decision'}),

    # データインポート
    path('import/evaluation/', ImportModelView.as_view(), name='import_evaluation', kwargs={'schema_name': 'Evaluation'}),
    path('import/decision/', ImportModelView.as_view(), name='import_decision', kwargs={'schema_name': 'Decision'}),
]
