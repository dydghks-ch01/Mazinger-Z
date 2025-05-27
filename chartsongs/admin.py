from django.contrib import admin
from .models import ChartSong

@admin.register(ChartSong)
class ChartSongAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'normalized_genre', 'short_lylics')
    search_fields = ('title', 'artist', 'normalized_genre', 'lylics')
    # readonly_fields = ('lylics',)  # 가사 읽기 전용, 수정하고 싶으면 이 문장 주석 처리

    def short_lylics(self, obj):
        if obj.lylics:
            return obj.lylics[:30] + '...' if len(obj.lylics) > 30 else obj.lylics
        return ""
    short_lylics.short_description = '가사 미리보기'