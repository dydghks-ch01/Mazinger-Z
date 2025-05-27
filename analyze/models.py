from django.db import models
from django.conf import settings

class UserSong(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    top3_emotions = models.JSONField(null=True, blank=True)  # 감성 태그용
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'title', 'artist')  # 🔥 중복 방지

    def __str__(self):
        return f"{self.title} - {self.artist} ({self.user.username})"

# class Song(models.Model):
#     title = models.CharField(max_length=255)
#     artist = models.CharField(max_length=255)
#     top2_emotions = models.JSONField(null=True, blank=True)
#     top3_emotions = models.JSONField(null=True, blank=True)  # ✅ 추가
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('title', 'artist')  # 🔥 중복 방지

#     def __str__(self):
#         return f"{self.title} - {self.artist}"