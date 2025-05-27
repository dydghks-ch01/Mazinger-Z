# mypage/urls.py
from django.urls import path, include
from . import views  # 여기서 views.mypage 등 다 처리

urlpatterns = [
    path('', views.mypage, name='mypage'),
    path('verify_password/', views.verify_password, name='verify_password'),  # ✅ 고쳤음
    path('user-generated-lyrics/', views.user_generated_lyrics, name='user_generated_lyrics'),  # ✅ 이 줄!
    path('music/', include('music_search.urls')),
    path('user-lovelist/', views.user_lovelist, name='user_lovelist'),  
    path('json/', views.support_post_list_json, name='support_post_list_json'), # ✅ 추가진섭
    path('support/json/', views.support_post_list_json, name='support_post_list_json_alias'),  # ✅ 추가진섭섭
]
