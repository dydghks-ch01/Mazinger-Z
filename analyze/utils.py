# ✅ 필요한 모듈들 import
import os
import json
import requests
from openai import OpenAI  # OpenAI GPT API
from decouple import config  # .env 파일로부터 키 불러오기
from bs4 import BeautifulSoup  # HTML 파싱
import lyricsgenius  # Genius API
import re, time
from datetime import datetime
from urllib.parse import quote_plus
import pandas as pd
import spotipy  # Spotify API
from spotipy.oauth2 import SpotifyClientCredentials


# ✅ 장르 캐시 딕셔너리 (반복 요청 줄이기 위함)
genre_cache = {}

# ✅ 외부 API 설정
GENIUS_TOKEN = config("GENIUS_ACCESS_TOKEN")
genius = lyricsgenius.Genius(GENIUS_TOKEN, skip_non_songs=True, remove_section_headers=True)

SPOTIFY_CLIENT_ID = config('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = config('SPOTIFY_CLIENT_SECRET')
LASTFM_API_KEY = config('LASTFM_API_KEY')

# ✅ OpenAI 클라이언트 생성
gpt_client = OpenAI(api_key=config("OPENAI_API_KEY"))

# ✅ Spotify 클라이언트 생성
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

# ✅ GPT로 감성 분석 요청 (0~1 점수)
def analyze_lyrics_emotions(lyrics: str) -> dict:
    prompt = f"""
    아래는 노래 가사입니다. 이 가사에 대해 다음 10가지 감정에 대해 0~1 점수로 분석해 주세요:
    감정: 사랑, 즐거움, 열정, 행복, 슬픔, 외로움, 그리움, 놀람, 분노, 두려움

    감성 분석 결과를 JSON 형식으로 반환해주세요.
    예시: 
    {{
      "사랑": 0.8,
      "슬픔": 0.2,
      "행복": 0.4,
      "열정": 0.7
    }}

    가사:
    {lyrics}
    """
    try:
        response = gpt_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print("🔥 감성 분석 오류:", e)
        return {"error": str(e)}

# ✅ 점수를 백분율(%)로 정규화
def normalize_emotion_scores(raw_scores: dict) -> dict:
    if "error" in raw_scores:
        return raw_scores
    total = sum(raw_scores.values())
    if total == 0:
        return raw_scores
    return {k: round((v / total) * 100, 2) for k, v in raw_scores.items()}

# ✅ GPT로 가사 키워드 7개 추출 (한국어)
def extract_keywords_from_lyrics(lyrics):
    prompt = f"""
    Generate 7 Korean hashtag-style keywords based on the mood, context, emotional tone, time, or place of the following song lyrics.

    - All keywords must be in **Korean**.
    - Output only a JSON array like: ["#이별", "#운동", "#새벽", "#혼자듣기좋은", "#감성", "#비오는날", "#클럽", "#우울", "#트렌디", "#클럽", "#봄", "#드라이빙"]
    
    Output only a JSON array like: ["#tag1", "#tag2", ..., "#tag7"]

    Lyrics:
    {lyrics}
    """
    try:
        response = gpt_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        result = response.choices[0].message.content.strip()
        return json.loads(result) if result.startswith("[") else []
    except Exception as e:
        print("❌ 키워드 추출 실패:", e)
        return []

# ✅ Last.fm API 기반 장르 추출 (보조 용도)
def get_lastfm_genre(title, artist):
    try:
        res = requests.get("http://ws.audioscrobbler.com/2.0/",
            params={"method": "track.getTopTags", "artist": artist, "track": title,
                    "api_key": LASTFM_API_KEY, "format": "json"})
        tags = res.json().get('toptags', {}).get('tag', [])
        return ', '.join([tag['name'] for tag in tags[:2]]) if tags else ''
    except:
        return ''

# ✅ 다양한 장르명 표기를 통일시키기 위한 매핑 테이블
GENRE_MAP = {
    'k-pop': '댄스', 'k-rap': '랩/힙합', 'k-ballad': '발라드', 'k-rock': '록/메탈',
    'soundtrack': 'OST', 'pop': '팝', 'r&b': '알앤비', 'hip hop': '랩/힙합',
    'indie': '인디', 'edm': '일렉트로닉', 'electronic': '일렉트로닉', 'house': '하우스',
    'techno': '테크노', 'jazz': '재즈', 'blues': '블루스', 'folk': '포크',
    'classical': '클래식', 'reggae': '레게'
}

# ✅ 위 장르 매핑 테이블 기반 정규화 함수
def normalize_genre(genre):
    if pd.isna(genre) or not genre:
        return '기타'
    genre_parts = [g.strip().lower() for g in genre.split(',')]
    for g in genre_parts:
        if g in GENRE_MAP:
            return GENRE_MAP[g]
    return genre  # 매핑 안된 장르는 그대로 반환

# ✅ Spotify API로 장르 추출
def get_spotify_genre(title, artist):
    try:
        res = sp.search(q=f"{title} {artist}", type='track', limit=1)
        track = res['tracks']['items'][0]
        artist_id = track['artists'][0]['id']
        artist_info = sp.artist(artist_id)
        return ', '.join(artist_info.get('genres', []))
    except:
        return ''

# ✅ 멜론 웹페이지에서 장르 추출 (크롤링)
def get_melon_genre(song_id):
    try:
        res = requests.get(f"https://www.melon.com/song/detail.htm?songId={song_id}",
                           headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        for dt in soup.select("div.meta > dl > dt"):
            if "장르" in dt.text:
                dd = dt.find_next_sibling("dd")
                return dd.text.strip() if dd else ''
    except:
        return ''

# ✅ 지니 웹페이지에서 장르 추출 (크롤링)
def get_genie_genre(song_id):
    try:
        res = requests.get(f"https://www.genie.co.kr/detail/songInfo?xgnm={song_id}",
                           headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        for dt in soup.select("div.info-zone dt"):
            if "장르" in dt.text:
                dd = dt.find_next_sibling("dd")
                a_tag = dd.find("a") if dd else None
                return a_tag.text.strip() if a_tag else (dd.text.strip() if dd else '')
    except Exception as e:
        print(f"❌ {e}")
        return ''

# ✅ 여러 플랫폼에서 장르 추출을 시도하고 캐시 처리까지 포함한 함수
def get_genre(song_id, title, artist, platform):
    key = (title.lower(), artist.lower())
    if key in genre_cache:
        print("🟡 [cache hit]")
        return genre_cache[key]

    print(f"🔍 [get_genre] Trying to get genre for: {title} - {artist}")
    genre = ''

    if platform == 'melon':
        genre = get_melon_genre(song_id)
        print("melon →", genre)
    if not genre:
        genre = get_genie_genre(song_id)
        print("genie →", genre)
    if not genre:
        genre = get_spotify_genre(title, artist)
        print("spotify →", genre)
    if not genre:
        genre = get_lastfm_genre(title, artist)
        print("lastfm →", genre)

    genre_cache[key] = genre or ''
    return genre or ''

# ✅ Genius API를 통한 가사 추출
def get_lyrics(title, artist, country="global"):
    try:
        song = genius.search_song(title, artist)
        if song and song.url:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(song.url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")

            lyrics_divs = soup.select("div[data-lyrics-container='true']")
            raw_lines = []
            for div in lyrics_divs:
                lines = div.get_text(separator="\n").split("\n")
                for line in lines:
                    cleaned = line.strip()

                    if not cleaned:
                        continue  # 빈 줄 제거

                    # ✅ 1. 언어/표시줄 제거
                    lowered = cleaned.lower()
                    if any(x in lowered for x in [
                        "translation", "romanization", "lyrics", "english", "français", "한국어", "日本語", "中文"
                    ]):
                        continue

                    # ✅ 2. 대괄호 감싸진 구간 제거 (ex. [Intro], [크러쉬 "미워" 가사])
                    if re.match(r"^\[.*\]$", cleaned):
                        continue

                    raw_lines.append(cleaned)

            full_lyrics = "\n".join(raw_lines)
            return full_lyrics.strip() if full_lyrics else "❌ 가사 없음"
        else:
            return "❌ 가사 없음"
    except Exception as e:
        print("❌ get_lyrics 실패:", e)
        return "❌ 가사 없음"



# ✅ Genius 웹페이지에서 발매일자 크롤링
def get_release_date_from_genius_url(song_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(song_url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        spans = soup.find_all("span")
        for span in spans:
            text = span.get_text(strip=True)
            if any(month in text for month in [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]):
                if any(char.isdigit() for char in text):
                    try:
                        return datetime.strptime(text, "%b. %d, %Y").date()
                    except ValueError:
                        pass
    except Exception as e:
        print("❌ 발매일 크롤링 실패:", e)
    return None

# ✅ 가사 내 불필요한 정보 정리 및 정제
def clean_lyrics(raw_lyrics: str) -> str:
    lines = raw_lyrics.strip().splitlines()

    # ✅ 1. 첫 줄이 비가사일 가능성이 높은 경우만 제거
    if lines:
        first_line = lines[0].lower()
        unwanted_keywords = ['provided to', 'official', 'youtube', 'music by', 'album', 'track', '℗', '©']
        if any(kw in first_line for kw in unwanted_keywords):
            lines = lines[1:]

    # ✅ 2. contributor, read more, translator 정보 제거
    lines = [line for line in lines if not re.search(r'(contributor|translator|read more)', line.lower())]

    # ✅ 3. 너무 많은 줄바꿈 정리
    lyrics = '\n'.join(lines)
    lyrics = re.sub(r'\n{3,}', '\n\n', lyrics)

    return lyrics.strip()
