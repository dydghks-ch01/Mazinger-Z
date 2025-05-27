from django.urls import path
from . import views
from .views import toggle_lovelist

urlpatterns = [
    path('', views.post_list, name='post_list'),                 # 게시판 메인
    path('new/', views.post_create, name='post_create'),         # 글쓰기 페이지
    path('<int:pk>/', views.post_detail, name='post_detail'),    # 상세 페이지
    path('<int:pk>/like/', views.like_post, name='like_post'),   # 좋아요
    path('comment/<int:comment_id>/reply/', views.comment_reply, name='comment_reply'),  # ✅ 대댓글
    path("scrap/<int:pk>/", views.scrap_post, name="scrap_post"),
    path('edit/<int:pk>/', views.post_edit, name='post_edit'),
    path('delete/<int:pk>/', views.post_delete, name='post_delete'),
    path('post/<int:pk>/delete/ajax/', views.post_delete_ajax, name='post_delete_ajax'),  # ✅ JS용 삭제
    path('toggle_lovelist/', toggle_lovelist, name='toggle_lovelist'),
    path('user-posts/', views.user_posts, name='user_posts'), # 진섭추가 
    path('post/<int:pk>/', views.post_detail, name='post_detail'), # 진섭추가 
    path('user-posts/', views.user_posts, name='user_posts'),  # ✅ MyPage 게시글 목록
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
]
