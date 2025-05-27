# music_search/scripts/save_tagged.py

from music_search.models import TaggedSong
from music_search.views import extract_tags_from_lyrics

def save_tagged_song(title, artist, lyrics):
    tags = extract_tags_from_lyrics(lyrics)
    if tags:
        TaggedSong.objects.create(title=title, artist=artist, lyrics=lyrics, tags=tags)
        print("✅ 저장 완료:", title, tags)
    else:
        print("❌ 태그 추출 실패:", title)
