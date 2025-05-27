from django.db import models
from django.conf import settings
from django.utils import timezone
from chartsongs.models import ChartSong # 0526 동건 추가

class Lovelist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    cover_url = models.URLField(blank=True, null=True)

    # 🔽 아래 필드들을 추가
    genre = models.CharField(max_length=255, blank=True, null=True)
    lyrics = models.TextField(blank=True, null=True)
    emotion_tags = models.JSONField(blank=True, null=True)
    keywords = models.JSONField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    genius_id = models.IntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_liked = models.BooleanField(default=True)
    song = models.ForeignKey(ChartSong, on_delete=models.CASCADE, null=True, blank=True)  # 0526 동건

    class Meta:
        unique_together = ('user', 'title', 'artist')

    def __str__(self):
        return f"{self.user} --- {self.title} by {self.artist}"
    
# 인기 태그 검색 저장 모델
class TagSearchLog(models.Model):
    tag = models.CharField(max_length=100)
    searched_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.tag