from django.shortcuts import render
from django.utils import timezone
# Create your views here.
from django.http import HttpResponse
import random
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, CharField
from django.db.models.functions import Cast
from chartsongs.models import ChartSong
# from analyze.models import Song
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .models import Lovelist
from .models import TagSearchLog
from collections import Counter
from django.utils.http import urlencode
#0526 동건 추가
import os
import numpy as np
import tensorflow as tf
import pickle
from django.conf import settings
import sys

# 0528 동건 추가
import datetime

# 0526 동건 추가
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
model = tf.keras.models.load_model(os.path.join(MODEL_DIR, 'final_model.h5'))
with open(os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl'), 'rb') as f:
    tfidf = pickle.load(f)

# 0527 동건 수정
def calculate_age(birthday):
    """
    생년월일(birthday)로부터 현재 나이를 계산하는 함수
    """
    today = datetime.date.today()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

def get_age_category(age):
    """
    나이를 받아서 나이대 카테고리(1~5)를 반환하는 함수
    """
    if age < 20:
        return 1
    elif age < 30:
        return 2
    elif age < 40:
        return 3
    elif age < 50:
        return 4
    else:
        return 5

def main(request):
    print("💡 main 함수 진입!", flush=True)

    # ✅ 퀴즈용 랜덤 곡 (가사 있는 곡 중 랜덤 1곡 선택)
    quiz_song = None
    songs = list(ChartSong.objects.filter(
        lylics__isnull=False
    ).exclude(lylics='').exclude(lylics__exact='None'))
    if songs:
        quiz_song = random.choice(songs)

    # ✅ 비로그인 fallback 추천: 랜덤 5곡
    all_cover_songs = list(ChartSong.objects.exclude(album_cover_url=''))
    random.shuffle(all_cover_songs)
    fallback_top5 = all_cover_songs[:5]
    top5 = fallback_top5  # 기본 추천

    if request.user.is_authenticated:
        print("✅ 유저 인증됨!", flush=True)

        # ✅ 사용자가 좋아요한 곡 ID 리스트
        liked_songs_qs = Lovelist.objects.filter(user=request.user, is_liked=True)
        liked_song_ids = list(liked_songs_qs.values_list('song_id', flat=True))
        print(f"✅ 좋아요한 song_id: {liked_song_ids}", flush=True)

        if liked_song_ids:
            # ✅ 좋아요한 곡 정보
            liked_songs = ChartSong.objects.filter(id__in=liked_song_ids)
            liked_texts = [f"{s.normalized_genre} {s.emotion_tags} {s.keywords}" for s in liked_songs]

            if liked_texts:
                # ✅ 좋아요곡들의 평균 벡터 계산
                liked_vecs = tfidf.transform(liked_texts)
                song_vec_mean = np.asarray(liked_vecs.mean(axis=0)).flatten()

                # ✅ 중첩 리스트를 평탄화하는 함수
                def flatten(l):
                    for el in l:
                        if isinstance(el, list):
                            yield from flatten(el)
                        else:
                            yield el

                # ✅ 감정/키워드 리스트를 평탄화
                emotion_list = [e for e in flatten([s.emotion_tags for s in liked_songs]) if e]
                keyword_list = [k for k in flatten([s.keywords for s in liked_songs]) if k]

                # ✅ 전체 감정/키워드 vocab 로드
                with open(os.path.join(MODEL_DIR, 'trained_emotions.pkl'), 'rb') as f:
                    all_emotions = pickle.load(f)
                with open(os.path.join(MODEL_DIR, 'trained_keywords.pkl'), 'rb') as f:
                    all_keywords = pickle.load(f)

                # ✅ 분포 벡터 계산 함수
                def build_dist(items, vocab):
                    count = {w: items.count(w) for w in vocab}
                    total = sum(count.values()) or 1
                    return [count.get(w, 0) / total for w in vocab]

                # ✅ 감정/키워드 분포 벡터 생성
                emotion_dist = build_dist(emotion_list, all_emotions)
                keyword_dist = build_dist(keyword_list, all_keywords)

                # ✅ 사용자 나이 계산 (없으면 30으로 기본값)
                if hasattr(request.user, 'birthday') and request.user.birthday:
                    user_age = calculate_age(request.user.birthday)
                else:
                    user_age = 30

                # ✅ 나이대 One-Hot 인코딩
                age_category = get_age_category(user_age)
                age_onehot = [1 if i == age_category else 0 for i in range(1, 6)]

                # ✅ 성별 One-Hot (없으면 'M'으로 기본값)
                user_gender = request.user.gender or 'M'
                gender_onehot = [1, 0] if user_gender == 'M' else [0, 1]

                # ✅ 최종 사용자 메타벡터 (나이대+성별)
                user_meta = np.array(age_onehot + gender_onehot)

                # ✅ 최종 사용자 벡터 (좋아요곡 평균벡터 + 사용자메타 + 감정 + 키워드)
                user_vector = np.hstack((song_vec_mean, user_meta, emotion_dist, keyword_dist))

                # ✅ 좋아요하지 않은 곡들로 추천 후보 리스트 생성
                not_liked_songs = ChartSong.objects.exclude(id__in=liked_song_ids)
                song_vectors_list = []
                song_objs_list = []
                for song in not_liked_songs:
                    song_text = f"{song.normalized_genre} {song.emotion_tags} {song.keywords}"
                    song_vec = tfidf.transform([song_text]).toarray().flatten()
                    sample = np.hstack((user_vector, song_vec))
                    song_vectors_list.append(sample)
                    song_objs_list.append(song)

                # ✅ 모델로 한 번에 배치 예측
                samples_array = np.array(song_vectors_list)
                preds = model.predict(samples_array, verbose=0).flatten()
                scores = list(zip(song_objs_list, preds))

                # ✅ 상위 20곡에서 3곡 랜덤으로 추출
                top20 = [s[0] for s in sorted(scores, key=lambda x: x[1], reverse=True)[:20]]
                print(f"🎵 모델 추천 후보 개수: {len(top20)}", flush=True)

                model_top3 = random.sample(top20, 3) if len(top20) >= 3 else top20
                print("\n🎯 [모델 추천곡 3곡 (랜덤 샘플링)]")
                for song in model_top3:
                    print(f"🎵 (모델추천) {song.title} by {song.artist}", flush=True)

                # ✅ 완전 랜덤 2곡 (모델 무관)
                all_songs_pool = list(not_liked_songs)
                random2 = random.sample(all_songs_pool, 2) if len(all_songs_pool) >= 2 else all_songs_pool
                print("\n🎯 [랜덤 추천곡 2곡 (완전 랜덤)]")
                for song in random2:
                    print(f"🎵 (랜덤) {song.title} by {song.artist}", flush=True)

                # ✅ 최종 5곡을 섞어서 사용자에게 표시
                combined5 = model_top3 + random2
                random.shuffle(combined5)
                top5 = combined5
                print("\n🎵 [사용자에게 최종 추천될 5곡 (모델3+랜덤2, 랜덤순서)]")
                for song in top5:
                    print(f"🎵 (최종) {song.title} by {song.artist}", flush=True)

    # ✅ 결과를 index.html로 렌더링
    return render(request, 'index.html', {
        'quiz_song': quiz_song,
        'cover_songs': top5,
        'popular_tags': get_popular_tags(),
    })
def preference_view(request):
    return render(request, "preference.html") # 메인 음악 취향 검사

# ✅ 추천 장르로 관련 곡 5개 불러오기
def recommend_by_genre(request):
    genre = request.GET.get("genre", "").lower()

    GENRE_MAP = {
        "r&b": ["r&b", "rnb", "알앤비", "groovy", "pop soul", "soul"],
        "랩/힙합": ["랩/힙합", "rap", "rage rap", "pop rap", "latin hip hop", "southern hip hop"],
        "발라드": ["발라드", "love songs", "sad", "ballad"],
        "일렉트로닉": ["일렉트로닉", "electropop", "synthpop", "synthwave", "downtempo", "trip hop"],
        "록/메탈": ["rock", "록/메탈", "alt-pop", "alternative", "album rock", "metal", "grunge"],
        "팝": ["팝", "pop", "indie pop", "folk pop", "soft pop", "pop rock"],
        "인디": ["인디", "indie", "bedroom pop", "indie rock", "indie pop", "hindi indie"],
        "ost": ["ost", "soundtrack"],
        "k-pop, edm": ["k-pop", "kpop", "edm", "전자음악", "댄스", "club"],
    }

    match_genres = []
    for key, keywords in GENRE_MAP.items():
        if genre in keywords or key in genre:
            match_genres = keywords
            break

    if not match_genres:
        return JsonResponse({"songs": []})

    # ✅ 복합 장르 문자열에도 대응 (icontains 기반 검색)
    query = Q()
    for keyword in match_genres:
        query |= Q(normalized_genre__icontains=keyword)

    songs = (
        ChartSong.objects.filter(query)
        .order_by("?")
        .values("title", "artist", "normalized_genre")[:10]  # ✅ 최대 10개로 확장 가능
    )

    return JsonResponse({"songs": list(songs)})

# 날씨 때문에 추가
# ✅ 위경도 → KMA 격자 좌표 변환 함수
def convert_to_grid(lat, lon):
    RE = 6371.00877  # 지구 반지름(km)
    GRID = 5.0       # 격자 간격(km)
    SLAT1 = 30.0     # 표준 위도1
    SLAT2 = 60.0     # 표준 위도2
    OLON = 126.0     # 기준점 경도
    OLAT = 38.0      # 기준점 위도
    XO = 43          # 기준점 X좌표
    YO = 136         # 기준점 Y좌표

    DEGRAD = math.pi / 180.0
    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf ** sn * math.cos(slat1)) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / (ro ** sn)

    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / (ra ** sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi: theta -= 2.0 * math.pi
    if theta < -math.pi: theta += 2.0 * math.pi
    theta *= sn

    x = int(ra * math.sin(theta) + XO + 0.5)
    y = int(ro - ra * math.cos(theta) + YO + 0.5)
    return {"nx": x, "ny": y}


@csrf_exempt
def get_weather_genre(request):
    sido = request.GET.get("sido")
    gugun = request.GET.get("gugun")

    if not sido or not gugun:
        return JsonResponse({"error": "지역 정보 누락"}, status=400)

    try:
        # ✅ Kakao 주소 검색 API로 위경도 얻기
        query = f"{sido} {gugun}"
        kakao_key = config("KAKAO_API_KEY")
        kakao_url = f"https://dapi.kakao.com/v2/local/search/address.json?query={query}"
        headers = {"Authorization": f"KakaoAK {kakao_key}"}
        kakao_response = requests.get(kakao_url, headers=headers)
        kakao_res = kakao_response.json()

        if "documents" not in kakao_res or not kakao_res["documents"]:
            return JsonResponse({"error": "좌표 변환 실패"}, status=404)

        lon = float(kakao_res["documents"][0]["x"])
        lat = float(kakao_res["documents"][0]["y"])

        # ✅ 위경도 → 격자 변환
        grid = convert_to_grid(lat, lon)
        nx, ny = grid["nx"], grid["ny"]

        # ✅ 기준 시각 계산 (초단기 실황: 10분 단위 → 가장 가까운 30분 전 시각 사용)
        now = datetime.now()
        minute = now.minute
        if minute < 45:
            now -= timedelta(hours=1)
        base_date = now.strftime("%Y%m%d")
        base_time = now.strftime("%H30")  # 초단기 실황 기준 시간

        # ✅ 기상청 초단기 실황 API 호출
        kma_key = config("KMA_SERVICE_KEY_ENCODED")
        kma_url = (
            f"http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
            f"?serviceKey={kma_key}&dataType=JSON&numOfRows=100&pageNo=1"
            f"&base_date={base_date}&base_time={base_time}&nx={nx}&ny={ny}"
        )

        res = requests.get(kma_url)
        print("KMA 요청 URL:", kma_url)
        print("KMA 응답 상태코드:", res.status_code)
        print("KMA 응답 본문:", res.text)

        data = res.json()

        try:
            items = data["response"]["body"]["items"]["item"]
        except Exception as e:
            return JsonResponse({
                "pty": "0",
                "note": "기상청 실황 데이터 없음",
                "kma_response": data
            }, status=200)

        # ✅ PTY 항목 추출 (실시간 관측값: obsrValue 사용)
        pty = next((item["obsrValue"] for item in items if item["category"] == "PTY"), "0")

        return JsonResponse({"pty": pty})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




# ✅ 시/도에 따른 구/군 리스트 반환
def get_guguns(request):
    sido = request.GET.get("sido")
    if not sido:
        return JsonResponse({"guguns": []})
    
    gugun_map = {
        "서울특별시": ["강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"],
        "부산광역시": ["강서구", "금정구", "기장군", "남구", "동구", "동래구", "부산진구", "북구", "사상구", "사하구", "서구", "수영구", "연제구", "영도구", "중구", "해운대구"],
        "대구광역시": ["남구", "달서구", "달성군", "동구", "북구", "서구", "수성구", "중구"],
        "인천광역시": ["강화군", "계양구", "남동구", "동구", "미추홀구", "부평구", "서구", "연수구", "옹진군", "중구"],
        "광주광역시": ["광산구", "남구", "동구", "북구", "서구"],
        "대전광역시": ["대덕구", "동구", "서구", "유성구", "중구"],
        "울산광역시": ["남구", "동구", "북구", "울주군", "중구"],
        "세종특별자치시": ["세종시"],
        "경기도": ["가평군", "고양시 덕양구", "고양시 일산동구", "고양시 일산서구", "과천시", "광명시", "광주시", "구리시", "군포시", "김포시", "남양주시", "동두천시", "부천시", "성남시 분당구", "성남시 수정구", "성남시 중원구", "수원시 권선구", "수원시 영통구", "수원시 장안구", "수원시 팔달구", "시흥시", "안산시 단원구", "안산시 상록구", "안성시", "안양시 동안구", "안양시 만안구", "양주시", "양평군", "여주시", "연천군", "오산시", "용인시 기흥구", "용인시 수지구", "용인시 처인구", "의왕시", "의정부시", "이천시", "파주시", "평택시", "포천시", "하남시", "화성시"],
        "강원특별자치도": ["강릉시", "고성군", "동해시", "삼척시", "속초시", "양구군", "양양군", "영월군", "원주시", "인제군", "정선군", "철원군", "춘천시", "태백시", "평창군", "홍천군", "화천군", "횡성군"],
        "충청북도": ["괴산군", "단양군", "보은군", "영동군", "옥천군", "음성군", "제천시", "증평군", "진천군", "청주시 상당구", "청주시 서원구", "청주시 청원구", "청주시 흥덕구", "충주시"],
        "충청남도": ["계룡시", "공주시", "금산군", "논산시", "당진시", "보령시", "부여군", "서산시", "서천군", "아산시", "예산군", "천안시 동남구", "천안시 서북구", "청양군", "태안군", "홍성군"],
        "전라북도": ["고창군", "군산시", "김제시", "남원시", "무주군", "부안군", "순창군", "완주군", "익산시", "임실군", "장수군", "전주시 덕진구", "전주시 완산구", "정읍시", "진안군"],
        "전라남도": ["강진군", "고흥군", "곡성군", "광양시", "구례군", "나주시", "담양군", "목포시", "무안군", "보성군", "순천시", "신안군", "여수시", "영광군", "영암군", "완도군", "장성군", "장흥군", "진도군", "함평군", "해남군", "화순군"],
        "경상북도": ["경산시", "경주시", "고령군", "구미시", "군위군", "김천시", "문경시", "봉화군", "상주시", "성주군", "안동시", "영덕군", "영양군", "영주시", "영천시", "예천군", "울릉군", "울진군", "의성군", "청도군", "청송군", "칠곡군", "포항시 남구", "포항시 북구"],
        "경상남도": ["거제시", "거창군", "고성군", "김해시", "남해군", "밀양시", "사천시", "산청군", "양산시", "의령군", "진주시", "창녕군", "창원시 마산합포구", "창원시 마산회원구", "창원시 성산구", "창원시 의창구", "창원시 진해구", "통영시", "하동군", "함안군", "함양군", "합천군"],
        "제주특별자치도": ["서귀포시", "제주시"]
    }

    guguns = gugun_map.get(sido, [])
    return JsonResponse({"guguns": guguns})

def quiz_song_view(request):
    songs = list(ChartSong.objects.filter(
        lylics__isnull=False
    ).exclude(
        lylics=''
    ).exclude(
        lylics__exact='None'
    ))

    if not songs:
        return render(request, 'quiz_song.html', {'quiz_song': None, 'show_gamecover': True})

    quiz_song = random.choice(songs)
    show_gamecover = not request.GET.get("no_cover")  # 핵심!
    return render(request, 'quiz_song.html', {
        'quiz_song': quiz_song,
        'show_gamecover': show_gamecover,
    })


def get_popular_tags(limit=5):
    tags = TagSearchLog.objects.values_list("tag", flat=True)
    counter = Counter(tags)
    return [tag for tag, _ in counter.most_common(limit)]

# 진섭이추가 
# 동건이수정
def search_results_view(request):
    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page')
    results = []

    # ✅ 인기 태그: 항상 노출
    popular_tags = get_popular_tags()

    if query:
        print(f"[🔍 DEBUG] query = '{query}'")

        matching_ids = set()

        # 👉 1. 해시태그 검색
        if query.startswith('#'):
            last_tag = request.session.get('last_searched_tag')
            if last_tag != query:
                TagSearchLog.objects.create(tag=query)
                request.session['last_searched_tag'] = query
            else:
                print(f"[🚫 SKIP] '{query}'는 직전 태그와 동일하므로 저장 생략")

            for song in ChartSong.objects.only('id', 'emotion_tags', 'keywords'):
                if isinstance(song.emotion_tags, list):
                    if query in [tag.strip() for tag in song.emotion_tags]:
                        print(f"[🎯 TAG MATCH - EMOTION] {song.title}")
                        matching_ids.add(song.id)
                if isinstance(song.keywords, list):
                    if query in [tag.strip() for tag in song.keywords]:
                        print(f"[🎯 TAG MATCH - KEYWORD] {song.title}")
                        matching_ids.add(song.id)

        # 👉 2. 일반 검색
        else:
            request.session['last_searched_tag'] = None  # 태그 세션 초기화

            # ✅ 실제 곡 존재 여부 확인 → 인기 검색어로 저장
            exists = ChartSong.objects.filter(
                Q(title__icontains=query) |
                Q(artist__icontains=query)
            ).exists()
            if exists:
                last_tag = request.session.get('last_searched_tag')
                if last_tag != query:
                    TagSearchLog.objects.create(tag=query)
                    request.session['last_searched_tag'] = query

            base_ids = ChartSong.objects.filter(
                Q(title__icontains=query) |
                Q(artist__icontains=query) |
                Q(lylics__icontains=query)
            ).values_list('id', flat=True)
            matching_ids.update(base_ids)

        # 👉 최종 결과 조회
        results_queryset = ChartSong.objects.filter(id__in=list(matching_ids)).distinct()
        paginator = Paginator(results_queryset, 10)
        results = paginator.get_page(page_number)

    return render(request, 'search_results.html', {
        'query': query,
        'results': results,
        'popular_tags': popular_tags,
    })

from collections import Counter
def get_popular_tags(limit=5):
    tags = TagSearchLog.objects.values_list("tag", flat=True)
    counter = Counter(tags)
    return [tag for tag, _ in counter.most_common(limit)]

def results_music_info_view(request):
    title = request.GET.get('title')
    artist = request.GET.get('artist')
    song_obj = ChartSong.objects.filter(title=title, artist=artist).first()

    is_liked = False
    liked_songs = []
    like_count = Lovelist.objects.filter(title=title, artist=artist,is_liked=True).count()  # ✅ 이 줄 추가

    if song_obj:
        # 기본 정보
        genre = song_obj.normalized_genre
        release_date = getattr(song_obj, 'release_date', '')
        cover_url = getattr(song_obj, 'album_cover_url', '')
        lyrics = getattr(song_obj, 'lylics', '') 
        emotion_tags = song_obj.emotion_tags  # 동건 추가
        keywords = song_obj.keywords          # 동건 추가

        # 동건 추가
        # ✅ 문자열이면 json.loads() 처리
        if isinstance(emotion_tags, str):
            try:
                emotion_tags = json.loads(emotion_tags)
            except:
                emotion_tags = []

        # 동건 추가
        if isinstance(keywords, str):
            try:
                keywords = json.loads(keywords)
            except:
                keywords = []

        song_info = {
            'title': title,
            'artist': artist,
            'genre': genre,
            'release_date': release_date,
            'cover_url': cover_url,
            'lyrics': lyrics, # ✅ 가사도 전달
            'emotion_tags': emotion_tags,   # 동건 추가
            'keywords': keywords,           # 동건 추가
        }


        if request.user.is_authenticated:
            is_liked = Lovelist.objects.filter(user=request.user, title=title, artist=artist, is_liked=True ).exists()
            liked_songs = Lovelist.objects.filter(user=request.user, is_liked=True).order_by('-updated_at')

    else:
        song_info = {}

    return render(request, 'results_music_info.html', {
        'song': song_info,
        'is_liked': is_liked,
        'liked_songs': liked_songs,
        'like_count': like_count,  # ✅ 추가
        })

def check_auth(request):
    return JsonResponse({"is_authenticated": request.user.is_authenticated})

@csrf_exempt
@login_required
def add_or_remove_like(request):
    data = json.loads(request.body)
    title = data.get("title")
    artist = data.get("artist")
    cover_url = data.get("cover_url", "")
    song = ChartSong.objects.filter(title=title, artist=artist).first() # 0526 동건 추가

    # 🎵 ChartSong 정보 조회
    chart_song = ChartSong.objects.filter(title=title, artist=artist).first()

    if not chart_song:
        return JsonResponse({"error": "곡 정보 없음"}, status=404)

    # ❤️ Lovelist에 존재하는지 확인
    obj, created = Lovelist.objects.get_or_create(
        user=request.user,
        title=title,
        artist=artist,
        defaults={
            'cover_url': chart_song.album_cover_url or cover_url,
            'genre': chart_song.normalized_genre,
            'lyrics': chart_song.lylics,  # 오타 주의
            'emotion_tags': chart_song.emotion_tags,
            'keywords': chart_song.keywords,
            'release_date': chart_song.release_date,
            'genius_id': chart_song.genius_id,
            'is_liked': True,
            'song': song,
        }
    )

    # 🔄 이미 존재하면 좋아요 상태만 반전 (삭제 아님)
    if not created:
        obj.is_liked = not obj.is_liked
        if (not obj.cover_url or obj.cover_url == "") and cover_url: # 0526 동건 수정(url 빈 문자열로 저장 방지)
            obj.cover_url = cover_url
        if obj.song is None and song: # 0526 동건 추가 ✅ song이 비어 있으면 지금 연결
            obj.song = song
        obj.save()
        count = Lovelist.objects.filter(title=title, artist=artist, is_liked=True).count()
        return JsonResponse({
            "status": "removed" if not obj.is_liked else "added",
            "count": count
        })


    # ➕ 새로 추가된 경우
    count = Lovelist.objects.filter(title=title, artist=artist, is_liked=True).count()
    return JsonResponse({"status": "added", "count": count})

# 0520 동건 수정

# 좋아요 목록 비동기 최신화 (직접 새로고침 x)
@login_required
def liked_songs_html(request):
    liked_songs = Lovelist.objects.filter(user=request.user, is_liked=True).order_by('-updated_at')
    html = ""
    for song in liked_songs:
        query = urlencode({'title': song.title, 'artist': song.artist})
        html += f"""
        <li>
          <a href='/music-info/?{query}'>
            <strong>{song.title}</strong><br>
            <span class='artist-name'>{song.artist}</span>
          </a>
        </li>
        """
    if not liked_songs:
        html = "<li>좋아요한 곡이 없습니다.</li>"
    return HttpResponse(html)