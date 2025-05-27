from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # ✅ 리스트에서 보여줄 필드
    list_display = (
        'username', 'email','nickname', 'birthday', 'phone_number', 'gender',
        'is_staff', 'is_active', 'profile_picture'
    )

    # ✅ 필터
    list_filter = ('username', 'is_staff', 'is_active')

    # ✅ 상세 보기에서 보여줄 필드 그룹
    fieldsets = (
        (None, {
            'fields': (
                'username', 'password', 'email', 'nickname',
                'birthday', 'phone_number', 'gender', 'profile_picture'
            )
        }),
        ('권한', {
            'fields': (
                'is_staff', 'is_active', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
    )

    # ✅ 사용자 추가 시 보여줄 필드
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2', 'nickname',
                'birthday', 'phone_number', 'gender',  'profile_picture',
                'is_staff', 'is_active'
            )
        }),
    )

    # ✅ 검색 필드와 정렬 기준
    search_fields = ('username', 'nickname')
    ordering = ('username',)
