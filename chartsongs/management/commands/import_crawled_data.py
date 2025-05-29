from django.core.management.base import BaseCommand
from chartsongs.models import ChartSong
import pandas as pd
import os, glob, time, requests, re, random, json
from openai import OpenAI
import lyricsgenius
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from decouple import config
from concurrent.futures import ThreadPoolExecutor
import unicodedata

# ✅ 환경변수
SPOTIFY_CLIENT_ID = config('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = config('SPOTIFY_CLIENT_SECRET')
LASTFM_API_KEY = config('LASTFM_API_KEY')
# GENIUS_API_KEY = config('GENIUS_ACCESS_TOKEN')
USERNAME = config('SPOTIFY_USERNAME')
PASSWORD = config('SPOTIFY_PASSWORD')


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print("🔥 감성 분석 오류:", e)
        return {"error": str(e)}

def extract_keywords_from_lyrics(lyrics):
    prompt = f"""
    Generate 7 Korean hashtag-style keywords based on the mood, context, emotional tone, time, or place of the following song lyrics.

    - All keywords must be in **Korean**.
    - Output only a JSON array like: ["이별", "운동", "새벽", "혼자듣기좋은", "감성", "비오는날", "클럽", "우울", "트렌디", "클럽", "봄", "드라이빙"]
    
    Output only a JSON array like: ["tag1", "tag2", ..., "tag7"]

    Lyrics:
    {lyrics}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        result = response.choices[0].message.content.strip()
        return json.loads(result) if result.startswith("[") else []
    except Exception as e:
        print("❌ 키워드 추출 실패:", e)
        return []

# ✅ Genius 키 3개 분산 처리용
GENIUS_KEYS = [
    config("GENIUS_ACCESS_TOKEN"),
    config("GENIUS_ACCESS_TOKEN_2"),
    config("GENIUS_ACCESS_TOKEN_3")
]

# ✅ 요청마다 무작위 Genius 인스턴스 선택
def get_genius_instance():
    key = random.choice(GENIUS_KEYS)
    return lyricsgenius.Genius(
        key,
        skip_non_songs=True,
        excluded_terms=["(Remix)", "(Live)"],
        remove_section_headers=True
    )

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

GENRE_MAP = {
    'k-pop': '댄스', 'k-rap': '랩/힙합', 'k-ballad': '발라드', 'k-rock': '록/메탈',
    'soundtrack': 'OST', 'pop': '팝', 'r&b': '알앤비', 'hip hop': '랩/힙합',
    'indie': '인디', 'edm': '일렉트로닉', 'electronic': '일렉트로닉', 'house': '하우스',
    'techno': '테크노', 'jazz': '재즈', 'blues': '블루스', 'folk': '포크',
    'classical': '클래식', 'reggae': '레게'
}

genre_cache = {}

# 유니코드 정규화
def normalize_title(title: str) -> str:
    """유니코드 정규화를 통해 이상 문자(P￦WER 등) 제거"""
    return unicodedata.normalize("NFKC", title)

def normalize_genre(genre):
    if pd.isna(genre) or not genre:
        return '기타'
    genre_parts = [g.strip().lower() for g in genre.split(',')]
    for g in genre_parts:
        if g in GENRE_MAP:
            return GENRE_MAP[g]
    # 매핑 안 되는 경우 → 원래 영문 장르 그대로 반환 (기타로 덮어쓰지 않음)
    return genre

def get_spotify_genre(title, artist):
    try:
        res = sp.search(q=f"{title} {artist}", type='track', limit=1)
        track = res['tracks']['items'][0]
        artist_id = track['artists'][0]['id']
        artist_info = sp.artist(artist_id)
        return ', '.join(artist_info.get('genres', []))
    except:
        return ''

# 앨범커버 추가
def get_spotify_album_cover(title, artist):
    try:
        res = sp.search(q=f"{title} {artist}", type='track', limit=1)
        items = res['tracks']['items']
        if items:
            return items[0]['album']['images'][0]['url']  # 가장 큰 이미지 URL
    except:
        pass
    return ''

def get_lastfm_genre(title, artist):
    try:
        res = requests.get("http://ws.audioscrobbler.com/2.0/",
            params={"method": "track.getTopTags", "artist": artist, "track": title,
                    "api_key": LASTFM_API_KEY, "format": "json"})
        tags = res.json().get('toptags', {}).get('tag', [])
        return ', '.join([tag['name'] for tag in tags[:2]]) if tags else ''
    except:
        return ''

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
    except:
        return ''

def get_genre(song_id, title, artist, platform):
    key = (title.lower(), artist.lower())
    if key in genre_cache:
        return genre_cache[key]
    genre = get_spotify_genre(title, artist) or get_lastfm_genre(title, artist)
    if not genre and platform == 'melon':
        genre = get_melon_genre(song_id)
    elif not genre and platform == 'genie':
        genre = get_genie_genre(song_id)
    genre_cache[key] = genre or ''
    time.sleep(0.1)
    return genre or ''

# def clean_lyrics(raw_lyrics):
#     cleaned = re.sub(r'\d+\s+Contributors', '', raw_lyrics)
#     cleaned = re.sub(r'Translations[\s\S]*?Lyrics', '', cleaned, flags=re.MULTILINE)
#     cleaned = re.sub(r'\[.*?\]|\(.*?\)', '', cleaned)
#     cleaned = re.sub(r'^[^\n]*Lyrics', '', cleaned, flags=re.MULTILINE)
#     return '\n'.join([line.strip() for line in cleaned.split('\n') if line.strip()])

def clean_lyrics(raw_lyrics: str) -> str:
    lines = raw_lyrics.strip().splitlines()

    # ✅ 1. 첫 줄이 설명문 (5단어 이상, [Verse] 아님)이면 제거
    if lines and len(lines[0].split()) >= 5 and not re.match(r"\[.*\]", lines[0]):
        lines = lines[1:]

    # ✅ 2. contributor, read more, translator 정보 제거
    lines = [line for line in lines if not re.search(r'(contributor|translator|read more)', line.lower())]

    # ✅ 3. 너무 많은 줄바꿈 정리
    lyrics = '\n'.join(lines)
    lyrics = re.sub(r'\n{3,}', '\n\n', lyrics)

    return lyrics.strip()

def fetch_lyrics_and_metadata(title, artist, retries=2, delay=4):
    genius = get_genius_instance()

    title = normalize_title(title)  # ✅ 유니코드 정규화

    # 1차 시도 (원본)
    for i in range(retries + 1):
        try:
            print(f"🔍 시도 {i+1} (원본): {title} - {artist}")
            song = genius.search_song(title, artist)
            if song and song.lyrics:
                if '-translation' in song.url:
                    print(f"⚠️ 번역 페이지 감지: {song.url} → 원곡 재시도")
                    break  # 👉 정제된 제목으로 넘어가기 위해 탈출
                lyrics = clean_lyrics(song.lyrics)
                release_date = get_genius_release_date(song.url)
                return lyrics, str(song.id), release_date
        except Exception as e:
            print(f"⚠️ 원본 요청 오류: {title} - {artist} → {e}")
        time.sleep(delay)

    # 2차 시도 (정제된 제목/아티스트로 재시도)
    cleaned_title = clean_title(title).split('feat')[0].strip()
    cleaned_artist = clean_artist_name(artist)

    for i in range(retries + 1):
        try:
            print(f"🔍 시도 {i+1} (정제): {cleaned_title} - {cleaned_artist}")
            song = genius.search_song(cleaned_title, cleaned_artist)
            if song and song.lyrics and '-translation' not in song.url:
                lyrics = clean_lyrics(song.lyrics)
                release_date = get_genius_release_date(song.url)
                return lyrics, str(song.id), release_date
        except Exception as e:
            print(f"⚠️ 정제 요청 오류: {cleaned_title} - {cleaned_artist} → {e}")
        time.sleep(delay)

    return '', None, ''




# def fetch_lyrics(artist, title):
#     try:
#         song = genius.search_song(title, artist)
#         if song and song.lyrics:
#             return clean_lyrics(song.lyrics)
#     except:
#         pass
#     return ''

# def fetch_lyrics(artist, title, retries=2, delay=2):
#     """Genius API에서 가사 요청 + 재시도"""
#     for i in range(retries + 1):
#         try:
#             print(f"🔍 시도 {i+1}: {title} - {artist}")
#             song = genius.search_song(title, artist)
#             if song and song.lyrics:
#                 return clean_lyrics(song.lyrics)
#         except Exception as e:
#             print(f"⚠️ 오류 발생: {title} - {artist} → {e}")
#         time.sleep(delay)
#     return ''

# # ✅ 번역 페이지 제외 + 3회 재시도 + 키 분산 적용
# def fetch_lyrics(artist, title, retries=2, delay=4):
#     for i in range(retries + 1):
#         try:
#             print(f"🔍 시도 {i+1}: {title} - {artist}")
#             genius = get_genius_instance()
#             song = genius.search_song(title, artist)
#             if song and song.lyrics:
#                 if '-translation' in song.url:
#                     print(f"⚠️ 번역 페이지 건너뜀: {song.url}")
#                     return ''
#                 return clean_lyrics(song.lyrics)
#         except Exception as e:
#             print(f"⚠️ 오류 발생: {title} - {artist} → {e}")
#         time.sleep(delay)
#     return ''

def clean_title(title: str) -> str:
    """괄호 등 부가 정보 제거"""
    return re.sub(r'\(.*?\)', '', title).strip()

def clean_artist_name(artist: str) -> str:
    """아티스트명에서 괄호 안 영문 우선 사용 → 없으면 한글로"""
    match = re.search(r'\(([A-Za-z0-9\- ]+)\)', artist)  # 영문 괄호 감지
    if match:
        return match.group(1).strip()
    return re.sub(r'\s*\(.*?\)', '', artist).strip()

def normalize_artist_name(artist: str) -> str:
    """아티스트명에서 괄호 안 영문 우선 사용 → 없으면 한글로"""
    match = re.search(r'\(([A-Za-z0-9\- ]+)\)', artist)  # 영문 괄호 감지
    if match:
        return match.group(1).strip()
    return re.sub(r'\s*\(.*?\)', '', artist).strip()


def fetch_lyrics(artist, title, retries=2, delay=4):
    genius = get_genius_instance()

    # ✅ 1차 시도: 원본 제목/아티스트 그대로
    for i in range(retries + 1):
        try:
            print(f"🔍 시도 {i+1} (원본): {title} - {artist}")
            song = genius.search_song(title, artist)
            if song and song.lyrics and '-translation' not in song.url:
                return clean_lyrics(song.lyrics)
        except Exception as e:
            print(f"⚠️ 원본 요청 오류: {title} - {artist} → {e}")
        time.sleep(delay)

    # ✅ 2차 시도: 정제된 제목/아티스트로 재요청
    cleaned_title = clean_title(title)
    cleaned_artist = clean_artist_name(artist)

    for i in range(retries + 1):
        try:
            print(f"🔍 시도 {i+1} (정제): {cleaned_title} - {cleaned_artist}")
            song = genius.search_song(cleaned_title, cleaned_artist)
            if song and song.lyrics and '-translation' not in song.url:
                return clean_lyrics(song.lyrics)
        except Exception as e:
            print(f"⚠️ 정제 요청 오류: {cleaned_title} - {cleaned_artist} → {e}")
        time.sleep(delay)

    return ''

def fetch_melon_chart():
    res = requests.get("https://www.melon.com/chart/index.htm", headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")
    chart = []
    for row in soup.select("div.service_list_song table tbody tr"):
        title_tag = row.select_one("div.ellipsis.rank01 a")
        artist_tag = row.select_one("div.ellipsis.rank02 a")
        link_tag = row.select_one("a[href*='goSongDetail']")
        if title_tag and artist_tag and link_tag:
            song_id = link_tag.get("href", "").split("'")[1]
            chart.append({'title': title_tag.text.strip(), 'artist': artist_tag.text.strip(),
                          'song_id': song_id, 'platform': 'melon'})
    return pd.DataFrame(chart)

def fetch_genie_chart():
    chart = []
    for page in range(1, 3):
        res = requests.get(f"https://www.genie.co.kr/chart/top200?pg={page}",
                           headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        for row in soup.select("table.list-wrap > tbody > tr"):
            title_tag = row.select_one("a.title")
            artist_tag = row.select_one("a.artist")
            onclick = title_tag.get("onclick", "") if title_tag else ""
            try:
                song_id = onclick.split("'")[1]
            except:
                continue
            if title_tag and artist_tag:
                chart.append({'title': title_tag.text.strip().replace("TITLE", "").strip(),
                              'artist': artist_tag.text.strip(),
                              'song_id': song_id, 'platform': 'genie'})
    return pd.DataFrame(chart)

def fetch_spotify_csv():
    today = datetime.now()
    date_str = (today - timedelta(days=(today.weekday() - 3) % 7 + 7)).strftime("%Y-%m-%d")
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": os.getcwd()}
    options.add_experimental_option("prefs", prefs)

    # 💡 충돌 방지: 새로운 임시 사용자 데이터 디렉토리 지정
    options.add_argument("--user-data-dir=/tmp/selenium_profile")
    # 💡 서버 환경일 경우 필수: 샌드박스/공유메모리 비활성화
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    try:
        driver.get("https://charts.spotify.com/charts/view/regional-global-weekly/latest")
        wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@data-testid="charts-login"]'))).click()
        wait.until(EC.url_contains("accounts.spotify.com"))
        wait.until(EC.presence_of_element_located((By.ID, "login-username"))).send_keys(USERNAME)
        wait.until(EC.element_to_be_clickable((By.ID, "login-button"))).click()
        time.sleep(3)
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//button[contains(text(), "Log in with a password")]'))).click()
        except:
            pass
        wait.until(EC.presence_of_element_located((By.ID, "login-password"))).send_keys(PASSWORD)
        wait.until(EC.element_to_be_clickable((By.ID, "login-button"))).click()
        time.sleep(5)
        driver.get(f"https://charts.spotify.com/charts/view/regional-global-weekly/{date_str}")
        wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-labelledby="csv_download"]'))).click()
        time.sleep(5)
    finally:
        driver.quit()

def fetch_spotify_chart():
    files = glob.glob('regional-global-weekly-*.csv')
    if not files:
        raise FileNotFoundError("❌ Spotify CSV 파일이 없습니다!")
    latest_file = max(files, key=os.path.getmtime)
    df = pd.read_csv(latest_file)
    if 'track_name' in df.columns and 'artist_names' in df.columns:
        df = df[['track_name', 'artist_names']].rename(columns={'track_name': 'title', 'artist_names': 'artist'})
    elif 'Track Name' in df.columns and 'Artist' in df.columns:
        df = df[['Track Name', 'Artist']].rename(columns={'Track Name': 'title', 'Artist': 'artist'})
    os.remove(latest_file)
    return df

# 발매일 크롤링
def get_genius_release_date(song_url: str):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(song_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        spans = soup.find_all("span")
        for span in spans:
            text = span.get_text(strip=True)
            if any(month in text for month in [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]) and any(char.isdigit() for char in text):
                try:
                    dt = datetime.strptime(text, "%b. %d, %Y")
                    return dt.date().isoformat()
                except ValueError:
                    continue  # 혹시 %b %d, %Y 형식일 수도?
                try:
                    dt = datetime.strptime(text, "%b %d, %Y")
                    return dt.date().isoformat()
                except ValueError:
                    continue
    except Exception as e:
        print("❌ 발매일 크롤링 실패:", e)
    return None


# class Command(BaseCommand):
#     help = '멜론, 지니, 스포티파이 차트 + 장르 + 가사 통합 저장'

#     def handle(self, *args, **options):
#         fetch_spotify_csv()
#         melon_df = fetch_melon_chart()
#         genie_df = fetch_genie_chart()
#         spotify_df = fetch_spotify_chart()
#         combined_df = pd.concat([melon_df, genie_df, spotify_df], ignore_index=True)
#         combined_df.drop_duplicates(subset=['title', 'artist'], inplace=True)
#         # combined_df = combined_df.tail(20)  # ✅ 주석 풀면 하위 20개만 실행

#         for _, row in combined_df.iterrows():
#             title, artist, song_id, platform = row.get('title'), row.get('artist'), row.get('song_id', ''), row.get('platform', 'spotify')
#             genre = get_genre(song_id, title, artist, platform)
#             normalized_genre = normalize_genre(genre)
#             obj, _ = ChartSong.objects.get_or_create(title=title, artist=artist, normalized_genre=normalized_genre)
#             if not obj.lylics:
#                 obj.lylics = fetch_lyrics(artist, title)
#                 obj.save()
#             print(f"✅ 저장 완료: {title} - {artist} ({normalized_genre})")

#         self.stdout.write(self.style.SUCCESS('✅ 모든 곡 DB 저장 및 가사/장르 업데이트 완료!'))

# def process_row(row):
#     title = row.get('title')
#     artist = row.get('artist')
#     song_id = row.get('song_id', '')
#     platform = row.get('platform', 'spotify')

#     genre = normalize_genre('')
#     album_cover = get_spotify_album_cover(title, artist)

#     obj, created = ChartSong.objects.get_or_create(
#         title=title,
#         artist=artist,
#         normalized_genre=genre,
#         defaults={'album_cover_url': album_cover}
#     )

#     if not obj.album_cover_url and album_cover:
#         obj.album_cover_url = album_cover
#         obj.save()

#     # ✅ 이미 가사 있음 → 발매일만 따로 저장 시도
#     if obj.lylics:
#         if not obj.release_date:
#             _, genius_id, genius_url = fetch_lyrics_with_id(artist, title)
#             release_date = get_genius_release_date(genius_url) if genius_url else ''
#             # ✅ 중복 genius_id 방지
#             if genius_id and ChartSong.objects.filter(genius_id=genius_id).exclude(id=obj.id).exists():
#                 return f"❌ 발매일 중복 건너뜀 (genius_id): {title} - {artist}"
#             if release_date:
#                 obj.release_date = release_date
#                 obj.genius_id = genius_id
#                 obj.save()
#                 return f"✅ 발매일만 저장: {title} - {artist}"
#         return f"⏩ SKIP (already has lyrics): {title} - {artist}"

#     # ✅ 가사 없음 → 전체 저장
#     time.sleep(3.5)  # 직렬 기준
#     lyrics, genius_id, genius_url = fetch_lyrics_with_id(artist, title)
#     release_date = get_genius_release_date(genius_url) if genius_url else ''

#     if lyrics:
#         if genius_id and ChartSong.objects.filter(genius_id=genius_id).exclude(id=obj.id).exists():
#             return f"❌ 중복 건너뜀 (genius_id): {title} - {artist}"
#         obj.lylics = lyrics
#         obj.genius_id = genius_id
#         obj.release_date = release_date
#         obj.save()
#         return f"✅ 저장 완료: {title} - {artist}"
#     else:
#         return f"❌ 가사 실패: {title} - {artist}"

def process_row(row):
    title = row.get('title')
    title = normalize_title(title)
    artist = normalize_artist_name(row.get('artist'))
    song_id = row.get('song_id', '')
    platform = row.get('platform', 'spotify')

    # ✅ 장르 추론 및 정제
    genre = get_genre(song_id, title, artist, platform)
    normalized_genre = normalize_genre(genre)

    # ✅ 앨범 커버
    album_cover = get_spotify_album_cover(title, artist)

    # ✅ 가사 + genius ID + 발매일
    lyrics, genius_id, release_date = fetch_lyrics_and_metadata(title, artist)

    # ✅ genius_id 중복 확인
    if genius_id and ChartSong.objects.filter(genius_id=genius_id).exists():
        print(f"⛔ 중복 genius_id 건너뜀: {title} - {artist}")
        return f"⛔ SKIP (중복 genius_id): {title} - {artist}"

    # ✅ 감정 태그 + 키워드 분석 (가사 있는 경우만)
    emotion_tags, keywords = [], []
    if lyrics:
        scores = analyze_lyrics_emotions(lyrics)
        print(f"🎯 감정 분석 결과: {scores}")
        if "error" not in scores:
            top3 = sorted(scores.items(), key=lambda x: -x[1])[:3]
            emotion_tags = [f"#{k}" for k, _ in top3]  # ✅ 해시태그로 저장
        raw_keywords = extract_keywords_from_lyrics(lyrics)
        keywords = [f"#{kw}" for kw in raw_keywords if kw]  # ✅ 해시태그로 저장
        print(f"🔑 키워드 추출 결과: {keywords}")

    # ✅ DB 저장: 동일한 title + artist가 있는 경우 가져옴
    obj, created = ChartSong.objects.get_or_create(
        title=title,
        artist=artist,
        defaults={
            'normalized_genre': normalized_genre,
            'album_cover_url': album_cover,
            'lylics': lyrics,
            'release_date': release_date if release_date else None,   # 0526 동건 추가
            'release_date': release_date,
            'genius_id': genius_id,
            'emotion_tags': emotion_tags,
            'keywords': keywords
        }
    )

    updated = False

    # 누락된 필드 업데이트
    if not obj.lylics and lyrics:
        obj.lylics = lyrics
        updated = True

    if not obj.album_cover_url and album_cover:
        obj.album_cover_url = album_cover
        updated = True

    if not obj.release_date and release_date:
        obj.release_date = release_date
        updated = True

    if not obj.genius_id and genius_id and not ChartSong.objects.filter(genius_id=genius_id).exclude(pk=obj.pk).exists():
        obj.genius_id = genius_id
        updated = True

    # ✅ emotion_tags 업데이트 여부 로깅
    if not obj.emotion_tags:
        if emotion_tags:
            obj.emotion_tags = emotion_tags
            updated = True
            print(f"✅ emotion_tags 업데이트됨: {title} - {artist} → {emotion_tags}")
        else:
            print(f"⚠️ GPT 분석 결과 없음: {title} - {artist}")

    if not obj.keywords and keywords:
        obj.keywords = keywords
        updated = True


    if updated:
        obj.save()
        return f"✅ 업데이트: {title} - {artist}"
    elif created:
        return f"✅ 신규 저장: {title} - {artist}"
    else:
        return f"⏩ SKIP: {title} - {artist}"






# genius 곡 id
def fetch_lyrics_with_id(artist, title, retries=2, delay=4):
    # 원본 검색
    for i in range(retries + 1):
        try:
            print(f"🔍 시도 {i+1} (원본): {title} - {artist}")
            genius = get_genius_instance()
            song = genius.search_song(title, artist)
            if song and song.lyrics:
                if '-translation' in song.url:
                    print(f"⚠️ 번역 페이지 건너뜀: {song.url}")
                    return '', None, None
                return clean_lyrics(song.lyrics), str(song.id), song.url
        except Exception as e:
            print(f"⚠️ 오류 발생: {title} - {artist} → {e}")
        time.sleep(delay)

    # 정제된 검색
    cleaned_title = clean_title(title)
    cleaned_artist = clean_artist_name(artist)
    for i in range(retries + 1):
        try:
            print(f"🔍 시도 {i+1} (정제): {cleaned_title} - {cleaned_artist}")
            genius = get_genius_instance()
            song = genius.search_song(cleaned_title, cleaned_artist)
            if song and song.lyrics:
                if '-translation' in song.url:
                    print(f"⚠️ 번역 페이지 건너뜀 (정제): {song.url}")
                    return '', None, None
                return clean_lyrics(song.lyrics), str(song.id), song.url
        except Exception as e:
            print(f"⚠️ 오류 발생 (정제): {cleaned_title} - {cleaned_artist} → {e}")
        time.sleep(delay)

    return '', None, None

class Command(BaseCommand):
    help = '병렬or직렬 로 차트 + 장르 + 가사 저장 (속도 제한 포함)'

    def handle(self, *args, **options):
        start = time.time() # 시작 시간

        self.stdout.write("🎧 차트 수집 시작...")

        fetch_spotify_csv()
        melon_df = fetch_melon_chart()
        genie_df = fetch_genie_chart()
        spotify_df = fetch_spotify_chart()

        combined_df = pd.concat([melon_df, genie_df, spotify_df], ignore_index=True)
        combined_df.drop_duplicates(subset=['title', 'artist'], inplace=True)
        # combined_df = combined_df.head(5)  # ✅ 일부만 실행

        self.stdout.write(f"🎶 총 {len(combined_df)}곡 저장 시작...")

        # 병렬
        # with ThreadPoolExecutor(max_workers=3) as executor:
        #     results = list(executor.map(process_row, combined_df.to_dict('records')))

        # 직렬
        results = []
        for row in combined_df.to_dict("records"):
            results.append(process_row(row))


        for line in results:
            print(line)

        self.stdout.write(self.style.SUCCESS("✅ 처리 완료"))

        end = time.time()  # 종료 시간
        elapsed = end - start
        self.stdout.write(f"\n⏱ 총 소요 시간: {elapsed:.1f}초 ({elapsed/60:.1f}분)")