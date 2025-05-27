from django.db import models
from django.contrib.postgres.fields import ArrayField  # PostgreSQL용 ArrayField

class ChartSong(models.Model):
    # 🎵 곡 제목
    title = models.CharField(max_length=255)

    # 🎤 아티스트명
    artist = models.CharField(max_length=255)

    # 🏷️ 정규화된 장르 이름 (예: 힙합, 발라드 등)
    normalized_genre = models.CharField(max_length=255)

    # 📝 가사 (오타는 나중에 수정 예정)
    lylics = models.TextField(blank=True, null=True)

    # 💬 감정 기반 태그 (예: ["#슬픔", "#위로", "#비오는날"])
    emotion_tags = models.JSONField(blank=True, null=True)

    # 🧠 가사 키워드 태그 (예: ["#사랑", "#계절", "#눈물"])
    keywords = models.JSONField(blank=True, null=True)

    # 🖼 앨범 커버 이미지 URL
    album_cover_url = models.URLField(blank=True, null=True)

    # 📅 발매일 (문자열로 저장 중)
    release_date = models.DateField(blank=True, null=True)

    # 🆔 Genius 고유 ID (중복 방지)
    genius_id = models.IntegerField(blank=True, null=True, unique=True)

    # 🔒 곡 중복 방지: 제목 + 아티스트 + 장르 조합 기준
    class Meta:
        unique_together = ('title', 'artist', 'normalized_genre')

    # 📌 Admin에 보여질 문자열 형식
    def __str__(self):
        short_lyrics = self.lylics[:30] + ('...' if self.lylics and len(self.lylics) > 30 else '') if self.lylics else ''
        return f"{self.title} - {self.artist} ({self.normalized_genre}) / {short_lyrics}"