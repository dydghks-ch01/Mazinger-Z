from django.contrib import admin
from .models import UserSong

@admin.register(UserSong)
class UserSongAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'top3_emotions', 'user', 'created_at')
    list_filter = ('user',)  # 사용자별로 필터링 가능하게 설정

# @admin.register(Song)
# class SongAdmin(admin.ModelAdmin):
#     list_display = ('title', 'artist', 'top2_emotions', 'created_at')