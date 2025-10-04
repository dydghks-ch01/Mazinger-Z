# SOSIC (Show your musictaste)
 팀 프로젝트용 사용자 취향 기반 음악 및 콘텐츠 추천 사이트

## 📝 프로젝트 소개

SOSIC 은 Django, 머신러닝, 오픈API를 활용하여 AI를 활용한 사용자 취향 기반 음악 및 콘텐츠 추천 웹 페이지를 제작한 프로젝트 입니다.

## ✅ 핵심 기능

- 음악 검색 및 가사 번역: 페이지에 없는 음악을 youtube API를 활용해 검색하고 검색된 가사를 정제 및 번역하여 볼 수 있도록 했습니다.
  - 불러온 가사 정제 및 번역 요청
 
    ```python
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
        

        cleaned_lyrics = clean_lyrics(song.lyrics)
        ko = translate_to("한국어", cleaned_lyrics)
        en = translate_to("영어", cleaned_lyrics)
        ja = translate_to("일본어", cleaned_lyrics)
        zh = translate_to("중국어", cleaned_lyrics)

        FullLyrics.objects.create(
            title=title, artist=artist, original=cleaned_lyrics,
            ko=ko, en=en, ja=ja, zh=zh
        )



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

    ```

  - GPT를 활용하여 번역


    ```python
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
    ```


- 가사 및 이미지 제작: GPT 모델을 활용하여 가사 및 앨범 이미지를 제작합니다.

  - 가사 및 이미지 제작
  
    ```python
    def generate_lyrics(request):
    if request.method == 'POST':
        prompt = request.POST.get('prompt')
        style = request.POST.get('style')
        language = request.POST.get('language')
        image_mode = request.POST.get('image_mode')
        fast_mode = (image_mode == 'skip')

        # 🔍 세션 및 시간 측정
        if not request.session.session_key:
            request.session.create()
        temp_user_id = request.session.session_key
        start_time = time.time()

        lang_phrase = {
            'english': " in English",
            'korean': " in Korean",
            'japanese': " in Japanese",
            'chinese': " in Chinese",
            'thai': " in Thai"
        }.get(language, "")

        # 🔍 GPT로 가사 생성 요청
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "user",
                    "content": f"""Please write complete lyrics for a {style} style song {lang_phrase} about "{prompt}".
                               Structure the lyrics clearly with parts like [Verse], [Chorus], and optionally [Bridge].
                               
                               Respond only in the format:
                               
                               제목: [song title]
                               가사:
                               [lyrics with labeled parts]
                               """
                }]
            )
            full_text = response.choices[0].message.content.strip()
            print("🔥 GPT 응답 확인:", full_text)

            if "제목:" in full_text and "가사:" in full_text:
                title = full_text.split("제목:")[1].split("가사:")[0].strip()
                lyrics = full_text.split("가사:")[1].strip()
            else:
                lines = full_text.splitlines()
                title = lines[0].strip() if lines else f"{prompt}의 노래"
                lyrics = "\n".join(lines[1:]).strip() if len(lines) > 1 else full_text

        except Exception as e:
            print("❌ GPT 호출 실패:", e)
            title = f"{prompt}의 노래"
            lyrics = "가사 생성에 실패했습니다. 다시 시도해주세요."

        # 🔍 이미지 생성
        cleaned_prompt = prompt.replace('"', '').replace("'", '')
        dalle_prompt = f"A {style} style album cover for a song about {cleaned_prompt}"
        image_filename = f"{uuid.uuid4()}.png"

        if fast_mode:
            print("🚀 Fast Mode: 이미지 생략 → 기본 이미지 사용")
            default_image_path = os.path.join(settings.BASE_DIR, 'lyricsgen', 'static', 'images', 'default_album.png')
            with open(default_image_path, 'rb') as f:
                image_content = f.read()
            image_filename = "default_album.png"
        else:
            try:
                image_response = client.images.generate(
                    model="dall-e-3",
                    prompt=dalle_prompt[:1000],
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                image_url = image_response.data[0].url
                image_content = requests.get(image_url, timeout=5).content
            except Exception as e:
                print("❌ 이미지 생성 실패:", e)
                with open('static/images/default_album.png', 'rb') as f:
                    image_content = f.read()

        elapsed_time = round(time.time() - start_time, 2)

        # 🔍 DB 저장
        new_lyrics = GeneratedLyrics(
            prompt=prompt,
            style=style,
            title=title,
            lyrics=lyrics,
            duration=elapsed_time,
            language=language,
            user=request.user if request.user.is_authenticated else None,
            temp_user_id=None if request.user.is_authenticated else temp_user_id
        )
        new_lyrics.image_file.save(image_filename, ContentFile(image_content))
        new_lyrics.save()

        return redirect(f"{reverse('lyrics_root')}?open_id={new_lyrics.id}")

    return redirect('lyrics_home')
    ```

- 가사 분석으로 태그 및 감정 키워드 추출: 음악 가사를 분석하여 태그 및 감정 키워드 추출로 곡을 분류할 기준점을 정했습니다.
  - 불러온 가사 정제 및 번역 요청
 
    ```python
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

    ```

- 음악 맞는 여행지 및 책 추천: GPT를 활용하여 음악에 맞는 추천 여행지와 책들을 제공합니다.
  - 불러온 가사 정제 및 번역 요청
    
    ```python
    client = OpenAI(api_key=config("OPENAI_API_KEY"))
    
    def search_song(request):
    if request.method == "GET":
        query = request.GET.get("q")
        count = int(request.GET.get("count", 3))

        if query:
            cache_key = f"gptrec:{query}:{count}"
            cached = cache.get(cache_key)
            if cached:
                return render(request, "results.html", cached)

            prompt = f"""
            노래 제목이 '{query}'야. 이 노래가사와 제목의 분위기에 어울리는 
            1. 책 {count}권 (제목, 작가, 추천 이유 포함),
            2. 여행지 {count}곳 (장소명과 추천 이유 포함)

            아래 형식으로 추천해줘:

            책 추천:
            1. '제목' - 작가 : 추천 이유
            2. ...

            여행지 추천:
            1. 장소명 : 추천 이유
            2. ...
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )

            gpt_result = response.choices[0].message.content
            lines = gpt_result.splitlines()

            book_lines = extract_lines("책 추천:", lines)[:count]
            travel_lines = extract_lines("여행지 추천:", lines)[:count]

            # 제목/장소만 먼저 파싱
            book_title_list = []
            books_raw = []
            for line in book_lines:
                match = re.match(r"\d+\.\s*['\"]?(.+?)['\"]?\s*-\s*(.+?)\s*:\s*(.+)", line)
                if match:
                    title, author, reason = match.groups()
                    book_title_list.append(title.strip())
                    books_raw.append({
                        "title": title.strip(),
                        "author": author.strip(),
                        "reason": reason.strip()
                    })

            place_name_list = []
            travels_raw = []
            for line in travel_lines:
                match = re.match(r"\d+\.\s*(.+?)\s*:\s*(.+)", line)
                if match:
                    place, reason = match.groups()
                    place_name_list.append(place.strip())
                    travels_raw.append({
                        "place": place.strip(),
                        "reason": reason.strip()
                    })

            # --- 비동기 Kakao 이미지 요청 병렬 실행 ---
            book_img_dict, place_img_dict = get_images_parallel(book_title_list, place_name_list)

            # 이미지 붙이기
            books = []
            for b in books_raw:
                b["image"] = book_img_dict.get(b["title"], "/static/no_book.png")
                books.append(b)
            travels = []
            for t in travels_raw:
                t["image"] = place_img_dict.get(t["place"], "/static/no_travel.png")
                travels.append(t)

            result_data = {
                "song": query,
                "books": books,
                "travels": travels,
            }
            cache.set(cache_key, result_data, timeout=60*60)

            return render(request, "results.html", result_data)

    return render(request, "search1.html")

    ```
