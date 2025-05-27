from django.conf import settings
from django.db import models

class SupportPost(models.Model):
    CATEGORY_CHOICES = [
        ('general', '일반 문의'),
        ('bug', '버그 제보'),
        ('feature', '기능 요청'),
        ('account', '계정 관련'),
        ('other', '기타'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')  # ✅ 추가
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class SupportReply(models.Model):
    post = models.OneToOneField(SupportPost, on_delete=models.CASCADE)
    responder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reply_text = models.TextField()
    replied_at = models.DateTimeField(auto_now_add=True)