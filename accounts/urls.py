from django.urls import path, include
from . import views
from .views import delete_lyrics
from mypage.views import user_generated_lyrics  # 다른 앱에서 뷰 import

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('mypage/', include('mypage.urls')),  # mypage 앱의 URL을 추가
    path('check_nickname/', views.check_nickname, name='check_nickname'),
    path('find_username/', views.find_username, name='find_username'),
    path('find_password/', views.find_password, name='find_password'),
    path('reset_password/<str:uid>/', views.reset_password, name='reset_password'),
    path('check_username/', views.check_username, name='check_username'),  # AJAX 용
    path('delete-lyrics/', delete_lyrics, name='delete_lyrics'),
    path('user-generated-lyrics/', user_generated_lyrics, name='user_generated_lyrics'),
    path('send_verification_code/', views.send_verification_code, name='send_verification_code'),
    path('verify_email_code/', views.verify_email_code, name='verify_email_code'),

]
