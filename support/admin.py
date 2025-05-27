from django.contrib import admin
from .models import SupportPost, SupportReply

# 답변을 문의글 안에서 인라인으로 보기
class SupportReplyInline(admin.StackedInline):
    model = SupportReply
    extra = 0
    readonly_fields = ('responder', 'replied_at')

@admin.register(SupportPost)
class SupportPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'user', 'created_at')
    search_fields = ('title', 'message')
    list_filter = ('category', 'created_at')
    inlines = [SupportReplyInline]  # ✅ 답변 인라인 포함

@admin.register(SupportReply)
class SupportReplyAdmin(admin.ModelAdmin):
    list_display = ('post', 'responder', 'replied_at')
    search_fields = ('reply_text',)
    list_filter = ('replied_at',)

