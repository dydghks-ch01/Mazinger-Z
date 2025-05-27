from django.shortcuts import render, redirect
from .utils import (
    get_lyrics,  # Genius에서 가사 크롤링
    analyze_lyrics_emotions,  # GPT로 감정 점수 분석
    extract_keywords_from_lyrics,  # GPT로 감성 키워드 추출
    get_genre,  # 장르 크롤링 (Melon/Genie/Spotify 등)
    normalize_genre,  # 장르 이름 통일화
    get_release_date_from_genius_url,  # Genius 웹페이지에서 발매일 추출
    normalize_emotion_scores,  # 감정 점수를 백분율로 정규화
    clean_lyrics  # 가사 전처리
)

from chartsongs.models import ChartSong
from lyricsgenius import Genius  # Genius API 클라이언트
from decouple import config  # .env 환경변수 로드
import random
from analyze.models import UserSong  # 사용자별 분석 결과 저장용 모델
from difflib import SequenceMatcher  # 가사 유사도 비교용




# ✅ Genius API 클라이언트 초기화
genius = Genius(
    config("GENIUS_ACCESS_TOKEN"),
    skip_non_songs=True,
    remove_section_headers=True
)

# ✅ 감성 분석 메인 뷰
# - 입력: 제목, 아티스트, 수동 가사 입력(optional)
# - 기능: 가사 분석, DB 저장 or 보완, 결과 리턴
# - 조건: 기존 DB에 존재 → 업데이트 / 없다면 → 분석 후 새로 저장

def analyze_input_view(request):
    if request.method == "POST":
        # 사용자 입력값 가져오기
        title_input = request.POST.get("title").strip()
        artist_input = request.POST.get("artist").strip()
        manual_lyrics = request.POST.get("manual_lyrics")
        country = request.POST.get("country", "global")

        try:
            # ✅ 기존 곡이 이미 DB에 있을 경우
            existing = ChartSong.objects.get(title=title_input, artist=artist_input)
            lyrics = clean_lyrics(existing.lylics)
            print("✅ DB에서 가사 불러옴")

            updated = False  # 변경된 항목이 있는지 확인용

            # 🔍 감정 태그 없으면 분석 후 저장
            if not existing.emotion_tags:
                emotion_scores = analyze_lyrics_emotions(lyrics)
                emotion_scores = normalize_emotion_scores(emotion_scores)
                top3_emotions = [k for k, v in sorted(emotion_scores.items(), key=lambda x: -x[1])[:3]]
                emotion_tags = [f"#{tag}" for tag in top3_emotions]  # DB 저장용은 # 붙임
                existing.emotion_tags = emotion_tags
                updated = True
            else:
                # 감정 분석은 다시 하지만 기존 태그 유지
                emotion_scores = analyze_lyrics_emotions(lyrics)
                emotion_scores = normalize_emotion_scores(emotion_scores)
                top3_emotions = [k for k, v in sorted(emotion_scores.items(), key=lambda x: -x[1])[:3]]
                emotion_tags = existing.emotion_tags

            # 🔍 키워드 없으면 추출
            if not existing.keywords:
                keywords = extract_keywords_from_lyrics(lyrics)
                existing.keywords = keywords
                updated = True
            else:
                keywords = existing.keywords

            # 🔍 장르 정보 없으면 크롤링
            if not existing.normalized_genre:
                platform = request.POST.get("platform", "melon")
                song_id = ""
                genre = get_genre(song_id, title_input, artist_input, platform)
                normalized_genre = normalize_genre(genre)
                existing.normalized_genre = normalized_genre
                updated = True

            # 🔍 발매일 없으면 Genius에서 추출
            if not existing.release_date:
                song = genius.search_song(title_input, artist_input)
                if song and song.url:
                    existing.release_date = get_release_date_from_genius_url(song.url)
                    if not existing.album_cover_url:
                        existing.album_cover_url = song.song_art_image_url
                    if not existing.genius_id:
                        existing.genius_id = song.id
                    updated = True

            if updated:
                existing.save()

        except ChartSong.DoesNotExist:
            # ✅ DB에 해당 곡이 없을 경우
            if manual_lyrics:
                # 🎯 수동 입력 가사 있는 경우
                lyrics = clean_lyrics(manual_lyrics.strip())

                if len(lyrics) < 30:
                    return render(request, "manual_lyrics_input.html", {
                        "title": title_input,
                        "artist": artist_input,
                    })

                # 분석 및 추출
                emotion_scores = analyze_lyrics_emotions(lyrics)
                emotion_scores = normalize_emotion_scores(emotion_scores)
                top3_emotions = [k for k, v in sorted(emotion_scores.items(), key=lambda x: -x[1])[:3]]
                emotion_tags = [f"#{tag}" for tag in top3_emotions]
                keywords = extract_keywords_from_lyrics(lyrics)

                # Genius에서 해당 곡 정보 탐색
                song = genius.search_song(title_input, artist_input)
                genius_id = song.id if song else None
                album_cover_url = song.song_art_image_url if song else None
                release_date = get_release_date_from_genius_url(song.url) if song and song.url else None

                # ✅ 가사 유사도 80% 이상일 경우에만 저장
                matched = False
                if song and song.lyrics:
                    genius_lyrics = clean_lyrics(song.lyrics)
                    similarity = SequenceMatcher(None, lyrics, genius_lyrics).ratio()
                    matched = similarity >= 0.8
                    print(f"🎯 가사 유사도: {similarity:.2f} → {'매치' if matched else '불일치'}")

                if genius_id and matched and not ChartSong.objects.filter(genius_id=genius_id).exists():
                    ChartSong.objects.create(
                        title=title_input,
                        artist=artist_input,
                        normalized_genre=None,
                        lylics=lyrics,
                        emotion_tags=emotion_tags,
                        keywords=keywords,
                        genius_id=genius_id,
                        album_cover_url=album_cover_url,
                        release_date=release_date
                    )

                    if request.user.is_authenticated:
                        try:
                            UserSong.objects.get(user=request.user, title=title_input, artist=artist_input)
                        except UserSong.DoesNotExist:
                            UserSong.objects.create(
                                user=request.user,
                                title=title_input,
                                artist=artist_input,
                                top3_emotions=emotion_tags
                            )

                # 결과 페이지 렌더링
                top3 = [(tag, emotion_scores[tag]) for tag in top3_emotions]
                return render(request, "analyze_result.html", {
                    "title": title_input,
                    "artist": artist_input,
                    "result": emotion_scores,
                    "top3": top3,
                    "keywords": keywords,
                    "lyrics": lyrics
                })

            # 🎯 수동 입력이 없으면 자동 크롤링 시도
            lyrics = get_lyrics(title_input, artist_input, country=country)
            lyrics = clean_lyrics(lyrics)

            if "❌" in lyrics or len(lyrics) < 30:
                return render(request, "manual_lyrics_input.html", {
                    "title": title_input,
                    "artist": artist_input,
                })

            # 분석 및 저장
            emotion_scores = analyze_lyrics_emotions(lyrics)
            emotion_scores = normalize_emotion_scores(emotion_scores)
            top3_emotions = [k for k, v in sorted(emotion_scores.items(), key=lambda x: -x[1])[:3]]
            emotion_tags = [f"#{tag}" for tag in top3_emotions]
            keywords = extract_keywords_from_lyrics(lyrics)

            platform = request.POST.get("platform", "melon")
            song_id = ""
            genre = get_genre(song_id, title_input, artist_input, platform)
            normalized_genre = normalize_genre(genre)

            song = genius.search_song(title_input, artist_input)
            genius_id = song.id if song else None
            album_cover_url = song.song_art_image_url if song else None
            release_date = get_release_date_from_genius_url(song.url) if song and song.url else None

            if genius_id and not ChartSong.objects.filter(genius_id=genius_id).exists():
                ChartSong.objects.create(
                    title=title_input,
                    artist=artist_input,
                    normalized_genre=normalized_genre,
                    lylics=lyrics,
                    emotion_tags=emotion_tags,
                    keywords=keywords,
                    genius_id=genius_id,
                    album_cover_url=album_cover_url,
                    release_date=release_date
                )

                if request.user.is_authenticated:
                    try:
                        UserSong.objects.get(user=request.user, title=title_input, artist=artist_input)
                    except UserSong.DoesNotExist:
                        UserSong.objects.create(
                            user=request.user,
                            title=title_input,
                            artist=artist_input,
                            top3_emotions=emotion_tags
                        )

        # ✅ 최종 감정 결과 렌더링
        top3 = [(tag, emotion_scores[tag]) for tag in top3_emotions]
        return render(request, "analyze_result.html", {
            "title": title_input,
            "artist": artist_input,
            "result": emotion_scores,
            "top3": top3,
            "keywords": keywords,
            "lyrics": lyrics
        })

    # ✅ GET 요청이면 입력폼 보여줌
    return render(request, "analyze_input.html")

# 홈 리디렉션 (기본 분석 페이지로 이동)
def home_redirect(request):
    return redirect('analyze')





# 감정 태그 기반 추천곡 뷰  #수정함
def recommend_by_emotion(request, tag):
    input_title = request.GET.get("title")
    input_artist = request.GET.get("artist")

    # 입력한 곡 제외
    if input_title and input_artist:
        all_songs = ChartSong.objects.exclude(
            title=input_title.strip(), artist=input_artist.strip()
        )
    else:
        all_songs = ChartSong.objects.all()

    # 감정 태그 필터링
    filtered_songs = [
        song for song in all_songs
        if f"#{tag.strip()}" in [t.strip() for t in song.emotion_tags or []]
    ]

    # 최대 5곡 랜덤 선택
    filtered_songs = random.sample(filtered_songs, min(len(filtered_songs), 5))

    return render(request, "recommendations.html", {
        "tag": tag,
        "songs": filtered_songs
    })
