from django.shortcuts import render, redirect, get_object_or_404
from openai import OpenAI
import os
import requests
import time
import uuid
from dotenv import load_dotenv
from django.core.files.base import ContentFile
from .models import GeneratedLyrics
from django.urls import reverse
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages

# ✅ 환경 변수 로딩 및 OpenAI 클라이언트 생성
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# ✅ 제목 추출 함수
def extract_title(lyrics_text):
    if "제목:" in lyrics_text:
        return lyrics_text.split("제목:")[1].split("가사:")[0].strip()
    return lyrics_text.splitlines()[0].strip() if lyrics_text else "제목 없음"

# ✅ 가사 보기 페이지 (GET)
def lyrics_home(request):
    print("🔥 세션 키:", request.session.session_key)  # ⭐️ 현재 세션 키 확인용

    open_id = request.GET.get('open_id')

    # 🔍 로그인/비로그인 상태에 따른 My Lyrics 목록 처리
    if request.user.is_authenticated:
        user_filter = {'user': request.user}
        all_lyrics = GeneratedLyrics.objects.filter(**user_filter).order_by('-is_favorite', '-created_at')
    else:
        temp_user_id = request.session.session_key
        if temp_user_id is None:
            # 🔥 세션이 아직 없으면 My Lyrics는 비활성화 (빈 배열)
            all_lyrics = []
        else:
            user_filter = {'user': None, 'temp_user_id': temp_user_id}
            all_lyrics = GeneratedLyrics.objects.filter(**user_filter).order_by('-is_favorite', '-created_at')

    # 🔍 선택된 가사 (가사 생성 결과 보기)
    selected_lyrics = None
    if open_id:
        try:
            if request.user.is_authenticated:
                user_filter = {'user': request.user}
            else:
                temp_user_id = request.session.session_key
                user_filter = {'user': None, 'temp_user_id': temp_user_id}
            selected_lyrics = GeneratedLyrics.objects.get(id=open_id, **user_filter)
        except GeneratedLyrics.DoesNotExist:
            selected_lyrics = None

    # 🔍 기본 이미지 여부 확인
    is_default_image = (
        selected_lyrics and
        selected_lyrics.image_file and
        "default_album" in os.path.basename(selected_lyrics.image_file.name)
    )

    return render(request, 'lyrics.html', {
        'all_lyrics': all_lyrics,
        'selected_lyrics': selected_lyrics,
        'prompt': selected_lyrics.prompt if selected_lyrics else '',
        'style': selected_lyrics.style if selected_lyrics else '',
        'lyrics': selected_lyrics.lyrics if selected_lyrics else '',
        'language': selected_lyrics.language if selected_lyrics else '',
        'elapsed_time': selected_lyrics.duration if selected_lyrics else '',
        'new_lyrics': selected_lyrics,
        'title': extract_title(selected_lyrics.lyrics) if selected_lyrics else '',
        'is_default_image': is_default_image,
    })

# ✅ 가사 생성 요청 (POST)
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

# ✅ 가사 수정
@require_POST
def edit_lyrics(request, pk):
    lyrics_obj = get_object_or_404(GeneratedLyrics, pk=pk)
    new_lyrics = request.POST.get('lyrics', '').strip()

    if request.user != lyrics_obj.user and not request.user.is_anonymous:
        return redirect('lyrics_root')

    lyrics_obj.lyrics = new_lyrics
    lyrics_obj.save()
    return redirect(f"{reverse('lyrics_root')}?open_id={pk}")

# ✅ 가사 삭제
@require_POST
def delete_lyrics(request, pk):
    lyrics_obj = get_object_or_404(GeneratedLyrics, pk=pk)

    if request.user != lyrics_obj.user and not request.user.is_anonymous:
        return redirect('lyrics_root')

    lyrics_obj.delete()
    return redirect('lyrics_root')

# ✅ 로그아웃 (세션 완전 초기화 + 새 세션 강제 발급)
def logout_view(request):
    logout(request)
    request.session.flush()
    request.session.create()
    return redirect('lyrics_root')

# ✅ 즐겨찾기 토글
@require_POST
def toggle_favorite(request, pk):
    lyric = get_object_or_404(GeneratedLyrics, pk=pk, user=request.user)
    lyric.is_favorite = not lyric.is_favorite
    lyric.save()
    return redirect(f"{reverse('lyrics_root')}?open_id={pk}")

# ✅ 이미지 다시 생성
@require_POST
def regenerate_image(request, pk):
    lyrics = get_object_or_404(GeneratedLyrics, pk=pk)

    dalle_prompt = f"A {lyrics.style} style album cover for a song about {lyrics.prompt}"
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

        image_filename = f"{uuid.uuid4()}.png"
        lyrics.image_file.save(image_filename, ContentFile(image_content))
        lyrics.save()
        print("✅ 이미지 생성 완료")
    except Exception as e:
        print("❌ 이미지 생성 실패:", e)
        messages.error(request, "이미지 생성에 실패했습니다.")

    return redirect(f"{reverse('lyrics_root')}?open_id={pk}")
