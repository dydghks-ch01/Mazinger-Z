# music_search/urls.py

from django.urls import path
from . import views
from .views import save_tagged_song_view

urlpatterns = [
    path('', views.search_view, name='music_search'),
    path('analyze-title/', views.analyze_title, name='analyze_title'),
    path('lyrics/', views.get_lyrics, name='get_lyrics'), 
    # path('translate-lyrics/', views.translate_lyrics, name='translate_lyrics'),
    path('autocomplete/', views.autocomplete, name='autocomplete'),  # 자동완성
    path('lyrics-info/', views.lyrics_info_view, name='lyrics_info'),
    path('save-tagged-song/', save_tagged_song_view),
    path('search/', views.search_view, name='search_view'),
    # path('toggle-favorite/', toggle_favorite, name='toggle_favorite'),
]
