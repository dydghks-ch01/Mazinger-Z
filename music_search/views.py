import os
import json
import requests
import lyricsgenius
from datetime import datetime
from dotenv import load_dotenv
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
from .models import TaggedSong, FullLyrics
from chartsongs.models import ChartSong
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
import unicodedata

# Spotify API 키 설정
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

spotify_client = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
))
print("✅ 확인:", os.environ.get("GENIUS_TOKEN"))

load_dotenv()

LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
GENIUS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
genius = lyricsgenius.Genius(GENIUS_TOKEN, skip_non_songs=True, excluded_terms=["(Remix)", "(Live)"])
genius.timeout = 15

client = OpenAI(api_key=settings.OPENAI_API_KEY)


# ✅ genre를 한국어로 변환하는 함수
GENRE_MAP = {
    'k-pop': '댄스', 'k-rap': '랩/힙합', 'k-ballad': '발라드', 'k-rock': '록/메탈',
    'soundtrack': 'OST', 'pop': '팝', 'r&b': '알앤비', 'hip hop': '랩/힙합',
    'indie': '인디', 'edm': '일렉트로닉', 'electronic': '일렉트로닉', 'house': '하우스',
    'techno': '테크노', 'jazz': '재즈', 'blues': '블루스', 'folk': '포크',
    'classical': '클래식', 'reggae': '레게'
}

def normalize_genre(genre):
    if not genre:
        return '기타'
    genre_parts = [g.strip().lower() for g in genre.split(',')]
    for g in genre_parts:
        if g in GENRE_MAP:
            return GENRE_MAP[g]
    return genre  # 못 찾으면 원문 그대로


# 1. 메인 검색 페이지 렌더링
def search_view(request):
    return render(request, 'search.html', {
        'youtube_api_key': settings.YOUTUBE_API_KEY,
    })

# 2. 검색어 자동완성 기능
def autocomplete(request):
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'suggestions': []})

    try:
        response = requests.get(
            'https://suggestqueries.google.com/complete/search',
            params={'client': 'firefox', 'ds': 'yt', 'q': query},
            timeout=5
        )
        result = response.json()
        suggestions = result[1] if len(result) > 1 else []
        return JsonResponse({'suggestions': suggestions})
    except:
        return JsonResponse({'suggestions': []})

# 3. GPT로 영상 제목에서 가수/곡명 추출
@csrf_exempt
def analyze_title(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        title = body.get('title', '')

        prompt = f"""
        다음 유튜브 영상 제목에서 가수와 곡명을 JSON 형식으로 추출해줘.
        - 형식: {{ "artist": ..., "title": ... }}
        - 피처링, 앨범 정보, 가사, OST, MV 등은 무시
        예: "{title}"
        """
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            content = response.choices[0].message.content
            parsed = json.loads(content)
        except Exception as e:
            parsed = {"artist": None, "title": None, "error": str(e)}

        return JsonResponse(parsed)
    return JsonResponse({'error': 'Only POST requests allowed.'}, status=405)

# 4. 가사 기반 상세 페이지 렌더링
def lyrics_info_view(request):
    artist = request.GET.get('artist', '').strip()
    title = request.GET.get('title', '').strip()
    video_id = request.GET.get('videoId')

    if not artist or not title or not video_id:
        return render(request, 'lyrics_info.html', {
            'error': 'Missing artist, title, or videoId'
        })

    return render(request, 'lyrics_info.html', {
        'artist': artist,
        'title': title,
        'video_id': video_id,
        'youtube_api_key': settings.YOUTUBE_API_KEY,
        'is_favorite': False,
    })


# ✅ 제목 정제: 괄호 등 제거
def clean_title(title: str) -> str:
    return re.sub(r'\(.*?\)', '', title).strip()

# ✅ 아티스트명 정제: 괄호 안 영문 우선, 없으면 괄호 제거
def clean_artist_name(artist: str) -> str:
    match = re.search(r'\(([A-Za-z0-9\- ]+)\)', artist)
    if match:
        return match.group(1).strip()
    return re.sub(r'\s*\(.*?\)', '', artist).strip()

# ✅ 유니코드 정규화 (혼합 문자 정리)
def normalize_title(title: str) -> str:
    return unicodedata.normalize("NFKC", title)

# ✅ 아티스트명 유니코드 정규화 (혼합 문자 정리)
def normalize_artist_name(artist: str) -> str:
    return unicodedata.normalize("NFKC", artist)

@csrf_exempt
def get_lyrics(request):
    if request.method == "POST":
        body = json.loads(request.body)
        artist = body.get("artist")
        title = body.get("title")

        if not artist or not title:
            return JsonResponse({"error": "Missing artist or title"}, status=400)

        try:
            existing = FullLyrics.objects.get(title=title, artist=artist)
            return JsonResponse({
                "lyrics": existing.original,
                "ko_lyrics": existing.ko,
                "en_lyrics": existing.en,
                "ja_lyrics": existing.ja,
                "zh_lyrics": existing.zh,
            })
        except FullLyrics.DoesNotExist:
            pass

        song = genius.search_song(title, artist)
        if not song or not song.lyrics:
            return JsonResponse({"error": "No song found on Genius"}, status=404)
        
        # 🔥 Genius가 아티스트/타이틀을 뒤바꿔 리턴할 경우 대비 → 강제로 입력값으로 덮어쓰기
        song.title = title
        song.artist = artist

        cleaned_lyrics = clean_lyrics(song.lyrics)
        ko = translate_to("한국어", cleaned_lyrics)
        en = translate_to("영어", cleaned_lyrics)
        ja = translate_to("일본어", cleaned_lyrics)
        zh = translate_to("중국어", cleaned_lyrics)

        FullLyrics.objects.create(
            title=title, artist=artist, original=cleaned_lyrics,
            ko=ko, en=en, ja=ja, zh=zh
        )

        try:
            # ✅ 정제: title, artist, 유니코드 + 괄호 제거
            title = normalize_title(clean_title(title))
            artist = normalize_artist_name(clean_artist_name(artist))

            # ✅ 앨범커버
            album_cover_url = song.song_art_image_url

            # ✅ 발매일
            release_str = getattr(song, 'release_date', None)
            release_date = parse_release_date(release_str)

            # ✅ 장르: Spotify → Last.fm → 한국어로 정규화!
            genre = get_spotify_genre(title, artist) or get_lastfm_genre(title, artist)
            normalized_genre = normalize_genre(genre) if genre else '기타'  # 🔥 여기서 한글로 변환!

            # ✅ 감정태그/키워드 추출
            emotion_tags = extract_tags_from_lyrics(cleaned_lyrics)
            keywords = extract_tags_from_lyrics(cleaned_lyrics)

            # ✅ ChartSong DB에 저장 (이미 있으면 업데이트만)
            obj, created = ChartSong.objects.get_or_create(
                title=title,
                artist=artist,
                defaults={
                    'normalized_genre': normalized_genre,
                    'album_cover_url': album_cover_url,
                    'lylics': cleaned_lyrics,
                    'release_date': release_date,
                    'genius_id': song.id,
                    'emotion_tags': [f"#{tag}" for tag in emotion_tags],
                    'keywords': [f"#{kw}" for kw in keywords],
                }
            )

            updated = False
            if not obj.lylics and cleaned_lyrics:
                obj.lylics = cleaned_lyrics
                updated = True
            if not obj.album_cover_url and album_cover_url:
                obj.album_cover_url = album_cover_url
                updated = True
            if not obj.release_date and release_date:
                obj.release_date = release_date
                updated = True
            if not obj.genius_id:
                obj.genius_id = song.id
                updated = True
            if not obj.normalized_genre and normalized_genre:
                obj.normalized_genre = normalized_genre
                updated = True
            if not obj.emotion_tags and emotion_tags:
                obj.emotion_tags = [f"#{tag}" for tag in emotion_tags]
                updated = True
            if not obj.keywords and keywords:
                obj.keywords = [f"#{kw}" for kw in keywords]
                updated = True

            if updated:
                obj.save()
                print(f"✅ ChartSong 업데이트됨: {artist} - {title}")
            elif created:
                print(f"✅ ChartSong 신규저장: {artist} - {title}")
            else:
                print(f"⏩ 이미 존재 (ChartSong): {artist} - {title}")

        except Exception as e:
            import traceback
            print("❌ ChartSong 저장 중 오류 발생")
            traceback.print_exc()


        return JsonResponse({
            "lyrics": cleaned_lyrics,
            "ko_lyrics": ko,
            "en_lyrics": en,
            "ja_lyrics": ja,
            "zh_lyrics": zh,
        })
    return JsonResponse({'error': 'Only POST requests allowed'}, status=405)


# 보조 함수: 가사 정제
def clean_lyrics(raw_lyrics: str) -> str:
    lines = raw_lyrics.strip().splitlines()

    # ✅ 1. Contributor, Translations 등 정보 라인 제거
    lines = [line for line in lines if not re.search(r'(contributor|translator|romanization|translations)', line.lower())]

    # ✅ 2. 가사 외 영어 설명, 특수문자 라인 제거 (예: "To ma so special lady" 등)
    lines = [line for line in lines if not re.match(r'^[a-zA-Z]', line.strip())]

    # ✅ 2.5. [Verse], [Chorus] 등 섹션 태그 제거
    lines = [line for line in lines if not re.match(r'^\[.*\]$', line.strip())]

    # ✅ 3. 빈 줄 제거
    lines = [line.strip() for line in lines if line.strip()]

    # ✅ 4. 중복 공백 라인 최소화
    cleaned = '\n'.join(lines)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned.strip()

# 보조 함수: 발매일 파싱
def parse_release_date(release_str):
    if release_str:
        for fmt in ("%Y-%m-%d", "%B %d, %Y"):
            try:
                return datetime.strptime(release_str, fmt).date()
            except:
                continue
    return None

def get_combined_genre(title, artist):
    lastfm_genre = get_lastfm_genre(title, artist)
    spotify_genre = get_spotify_genre(title, artist)

    combined_genres = [g for g in [spotify_genre, lastfm_genre] if g]
    return ', '.join(combined_genres[:2]) if combined_genres else "기타"

def get_spotify_genre(title, artist):
    try:
        results = spotify_client.search(q=f'track:{title} artist:{artist}', type='track', limit=1)
        tracks = results.get('tracks', {}).get('items', [])
        if not tracks:
            return ''
        
        artist_id = tracks[0]['artists'][0]['id']
        artist_info = spotify_client.artist(artist_id)
        genres = artist_info.get('genres', [])
        return ', '.join(genres[:2]) if genres else ''
    except Exception as e:
        print(f"Spotify genre fetch error: {e}")
        return ''

# Last.fm에서 장르 불러오기
def get_lastfm_genre(title, artist):
    try:
        res = requests.get("http://ws.audioscrobbler.com/2.0/", params={
            "method": "track.getTopTags",
            "artist": artist,
            "track": title,
            "api_key": LASTFM_API_KEY,
            "format": "json"
        })
        data = res.json()
        tags = data.get('toptags', {}).get('tag', [])
        valid_tags = [tag['name'] for tag in tags if tag['name'].lower() not in {'기타', 'other', 'unknown'}]
        return ', '.join(valid_tags[:2]) if valid_tags else ''
    except:
        return ''

# GPT 번역 보조
def translate_to(language, lyrics):
    prompt = f"{lyrics}\n\nTranslate to {language}:"
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except:
        return ""

# GPT 태그 추출
def extract_tags_from_lyrics(lyrics):
    prompt = f"""
    다음 노래 가사를 읽고, 가사의 주제 또는 분위기를 나타내는 한국어 태그 3개를 배열 형태로만 제공하세요. 
    반드시 아래 예시와 같은 형식으로 답하세요.
    예시: ["사랑", "이별", "슬픔"]

    가사:
    {lyrics}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        result = response.choices[0].message.content.strip()

        # 더 안정적인 JSON 파싱
        tags = json.loads(result)
        if isinstance(tags, list) and len(tags) == 3:
            return tags
        else:
            print(f"Invalid tags format: {result}")
            return []
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return []
    except Exception as e:
        print(f"❌ GPT error: {e}")
        return []


# 태그와 곡 DB 저장
@csrf_exempt
def save_tagged_song_view(request):
    data = json.loads(request.body)
    title, artist, lyrics = data.get("title"), data.get("artist"), data.get("lyrics")
    if TaggedSong.objects.filter(title=title, artist=artist).exists():
        return JsonResponse({"status": "skipped"})
    TaggedSong.objects.create(title=title, artist=artist, lyrics=lyrics, tags=extract_tags_from_lyrics(lyrics))
    return JsonResponse({"status": "success"})
