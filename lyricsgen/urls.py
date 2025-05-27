# lyricsgen/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.lyrics_home, name='lyrics_root'),  
    path('generate/', views.generate_lyrics, name='generate_lyrics'),
    path('lyrics/', views.lyrics_home, name='lyrics'),
    path('edit/<int:pk>/', views.edit_lyrics, name='edit_lyrics'),
    path('delete/<int:pk>/', views.delete_lyrics, name='delete_lyrics'),
    path('logout/', views.logout_view, name='logout'),
    path('lyrics/favorite/<int:pk>/', views.toggle_favorite, name='toggle_favorite'), # 즐겨찾기
    path('lyrics/regenerate-image/<int:pk>/', views.regenerate_image, name='regenerate_image'), # 빠른 가사 생성 이미지

]
