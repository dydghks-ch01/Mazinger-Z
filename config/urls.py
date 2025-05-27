"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('main.urls')),            # 메인 화면
    path('lyrics/', include('lyricsgen.urls')), # 가사 생성 앱
    path('accounts/', include('accounts.urls')), # 회원가입 로그인 로그아웃
    path('mypage/', include('mypage.urls')),  # mypage 앱의 URL을 포함
    path('analyze/', include('analyze.urls')),  # analyze 앱 연결
    path('music/', include('music_search.urls')), # music_search 앱 연결
    path('recommend/', include('recommendations.urls')), # recommendations 앱연결
    path('accounts/', include('accounts.urls')),
    path('board/', include('board.urls')), #board 앱 연결
    path('support/', include('support.urls')), #고객센터


]

# 이미지(= media 파일) 접근을 가능하게 함
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
