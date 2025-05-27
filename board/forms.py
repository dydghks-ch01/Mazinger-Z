# board/forms.py

from django import forms
from .models import Post, Comment
from django.forms.widgets import ClearableFileInput

# 🎯 게시글 작성 폼 정의 (Post 모델 기반)
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'description', 'thumbnail']  # 사용자가 입력할 필드들

        # 폼 필드에 CSS 클래스와 placeholder 추가
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '제목 입력'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': '설명 입력'}),
            'thumbnail': ClearableFileInput(),  # ✅ 위젯 지
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ✅ '취소' 체크박스 제거
        self.fields['thumbnail'].widget.clear_checkbox_label = ''
        self.fields['thumbnail'].widget.template_name = 'django/forms/widgets/file.html'
            
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'parent']  # ✅ parent 필드 포함
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
            'parent': forms.HiddenInput()
        }

