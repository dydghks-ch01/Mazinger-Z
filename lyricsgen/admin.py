from django.contrib import admin
from .models import GeneratedLyrics

@admin.register(GeneratedLyrics)
class GeneratedLyricsAdmin(admin.ModelAdmin):
    list_display = ('user', 'prompt', 'style', 'language', 'created_at')  # 사용자, 프롬프트, 스타일, 생성 시간 등
    search_fields = ('user__username', 'prompt', 'lyrics')  # 사용자 이름, 프롬프트, 가사 내용으로 검색 가능
    list_filter = ('user',)  # 사용자별로 필터링 가능하게 설정
    actions = ['delete_selected']  # ✅ 삭제 버튼 표시
