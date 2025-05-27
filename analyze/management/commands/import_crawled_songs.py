import requests
from bs4 import BeautifulSoup
import re
import time
from django.core.management.base import BaseCommand
from analyze.models import Song
from analyze.utils import get_lyrics, analyze_lyrics_emotions, normalize_emotion_scores, get_standard_artist_name

def clean_title(raw_title):
    blacklist = ['mv', 'm/v', 'official', 'video', 'topic', '[sub]', '🎼', 'live', 'performance', 'audio', 'smtown', 'theblacklabel', 'feat.', 'ft.']
    pattern = r'\b(' + '|'.join(map(re.escape, blacklist)) + r')\b'
    cleaned = re.sub(pattern, '', raw_title, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def get_melon_chart(limit=50):
    url = 'https://www.melon.com/chart/index.htm'
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, 'html.parser')
    songs = []

    titles = [tag.text.strip() for tag in soup.select('div.ellipsis.rank01 a')]
    artists = [tag.text.strip() for tag in soup.select('div.ellipsis.rank02 span.checkEllipsis')]

    for title, artist in zip(titles[:limit], artists[:limit]):
        songs.append({'title': title, 'artist': artist})

    return songs

class Command(BaseCommand):
    help = 'Melon 차트 → 가사 분석 → DB 저장'

    def handle(self, *args, **kwargs):
        melon_songs = get_melon_chart(limit=50)

        self.stdout.write(f"✅ 총 {len(melon_songs)}곡 수집됨")

        seen = set()
        unique_songs = []
        for song in melon_songs:
            key = (song['title'].lower(), song['artist'].lower())
            if key not in seen:
                seen.add(key)
                unique_songs.append(song)

        self.stdout.write(f"✅ 중복 제거 후 {len(unique_songs)}곡 처리 시작")

        for item in unique_songs:
            time.sleep(2)

            raw_title = item['title'].strip()
            cleaned_title = clean_title(raw_title).lower()

            artist_input = item['artist'].strip()
            artist = get_standard_artist_name(artist_input).lower()

            if Song.objects.filter(title=cleaned_title, artist=artist).exists():
                self.stdout.write(self.style.WARNING(f"⚠️ 이미 존재함: {cleaned_title} - {artist}"))
                continue

            try:
                lyrics = get_lyrics(cleaned_title, artist)
                if "❌" in lyrics or len(lyrics) < 30:
                    self.stdout.write(self.style.WARNING(f"⚠️ 가사 실패: {cleaned_title} - {artist}"))
                    continue

                raw_result = analyze_lyrics_emotions(lyrics)
                if "error" in raw_result:
                    self.stdout.write(self.style.WARNING(f"⚠️ 분석 실패: {cleaned_title} - {artist}"))
                    continue

                result = normalize_emotion_scores(raw_result)
                top2 = [k for k, _ in sorted(result.items(), key=lambda x: x[1], reverse=True)[:2]]

                Song.objects.create(
                    title=cleaned_title,
                    artist=artist,
                    top2_emotions=top2
                )
                self.stdout.write(self.style.SUCCESS(f"✅ 저장 완료: {cleaned_title} - {artist}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ 예외 발생: {cleaned_title} - {artist} → {e}"))
