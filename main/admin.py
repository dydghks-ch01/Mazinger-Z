from django.contrib import admin

from .models import Lovelist, TagSearchLog
from django.db.models import Count, Max

@admin.register(Lovelist)
class LovelistAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'artist', 'cover_url')

@admin.register(TagSearchLog)
class TagSearchLogAdmin(admin.ModelAdmin):
    list_display = ('tag', 'search_count', 'latest_search')
    search_fields = ('tag',)

    def get_queryset(self, request):
        # ✅ 원래 모델 인스턴스를 유지한 채 annotate만 적용
        qs = super().get_queryset(request)
        return qs.annotate(
            _search_count=Count('tag'),
            _latest_search=Max('searched_at')
        )

    def search_count(self, obj):
        return getattr(obj, '_search_count', 0)
    search_count.short_description = '검색 횟수'

    def latest_search(self, obj):
        return getattr(obj, '_latest_search', None)
    latest_search.short_description = '최근 검색일'