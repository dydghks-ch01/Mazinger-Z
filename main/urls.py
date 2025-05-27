from django.urls import path, include
from . import views
from .views import preference_view, quiz_song_view, search_results_view, results_music_info_view
from .views import preference_view, get_guguns # 메인 음악 취향 검사


urlpatterns = [
    path('', views.main, name='main'),
    path('music/', include('music_search.urls')), # music_search 앱 연결
    path('accounts/', include('accounts.urls')),  # accounts 앱의 URL을 포함시킴
    path('accounts/', include('django.contrib.auth.urls')),  # ✅ Django auth 추가
    path('lyricsgen/', include('lyricsgen.urls')),  # lyricsgen 앱의 URL을 포함시킴
    path('mypage/', include('mypage.urls')),  # mypage 앱의 URL을 포함시킴
    path('analyze/', include('analyze.urls')),  # analyze 앱 연결
    path('recommend/', include('recommendations.urls')), # recommendations 앱연결
    path('preference/', preference_view, name='preference'), # 메인 음악 취향 검사
    path("recommend_by_genre/", views.recommend_by_genre, name="recommend_by_genre"), # 메인 음악 취향 검사 추천 음악
    path('get_weather_genre/', views.get_weather_genre, name='get_weather_genre'), # 음악 취향 검사에서 날씨 조회
    path('get_guguns/', get_guguns, name='get_guguns'), # 음악 취향 검사에서 날씨 조회
    path('quiz_song/', quiz_song_view, name='quiz_song'), # 음악퀴즈
    path('search/', search_results_view, name='search_results'),#진섭이 추가
    path('music-info/', results_music_info_view, name='music_info'),#진섭이 추가
    path("check-auth/", views.check_auth, name="check_auth"),
    path("toggle-like/", views.add_or_remove_like, name="toggle_like"),
    path('board/', include('board.urls')),  # 🔥 게시판 앱 연결
    path("liked-songs-html/", views.liked_songs_html, name="liked_songs_html"),  # 0520 동건 추가 좋아요 목록 비동기 최신화
    path("lyrics-info/", views.results_music_info_view, name="results_music_info_view"), #analyze 감성 추천 곡에서 넘어오는거 # 민수가 추가함
]
