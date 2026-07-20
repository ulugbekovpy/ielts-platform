from django.urls import path
from .views import reading_test_view, daily_reading_view, listening_test_view, daily_listening_view, daily_vocabulary_view

urlpatterns = [
    # Единый URL для отображения теста (GET) и сохранения результатов (POST)
    path('reading/test/<int:test_id>/', reading_test_view, name='reading_test'),
    path('reading/', daily_reading_view, name='reading'),
    path('listening/test/<int:test_id>/', listening_test_view, name='listening_test'),
    path('listening/', daily_listening_view, name='listening'),
    # path('writing/test/<int:test_id>/', writing_test_view, name='writing_test'),
    path('vocabulary/', daily_vocabulary_view, name='vocabulary'),
]