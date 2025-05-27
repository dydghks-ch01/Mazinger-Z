from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_redirect, name='home_redirect'),  # 홈 경로
    path('analyze/', views.analyze_input_view, name='analyze'),  # 분석 입력 페이지
    path('result/', views.analyze_input_view, name='analyze_result'),  # 결과 페이지
    path('recommend/<str:tag>/', views.recommend_by_emotion, name='recommend_by_emotion'),  # 감정 추천 페이지
]