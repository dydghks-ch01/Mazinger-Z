from django.shortcuts import render
from openai import OpenAI
from decouple import config
import requests
import re
from django.core.cache import cache
import aiohttp
import asyncio

client = OpenAI(api_key=config("OPENAI_API_KEY"))

def extract_lines(start_tag, lines):
    result = []
    collecting = False
    for line in lines:
        if start_tag in line:
            collecting = True
            continue
        if collecting and re.match(r"^\d+\.", line.strip()):
            result.append(line.strip())
        elif collecting and not line.strip():
            break
    return result

# --- 비동기 Kakao 이미지 함수 ---
async def fetch_kakao_book_image(session, title):
    cache_key = f"book_img:{title}"
    img = cache.get(cache_key)
    if img:
        return title, img

    headers = {"Authorization": f"KakaoAK {config('KAKAO_API_KEY')}"}
    params = {"query": title, "sort": "accuracy"}
    url = "https://dapi.kakao.com/v3/search/book"
    try:
        async with session.get(url, headers=headers, params=params, timeout=2) as response:
            data = await response.json()
            if data.get("documents"):
                for book in data["documents"]:
                    if book.get("thumbnail") and book.get("width", 0) > 400 and book.get("height", 0) > 300:
                        cache.set(cache_key, book["thumbnail"], timeout=60*60*24)
                        return title, book["thumbnail"]
                thumbnail = data["documents"][0].get("thumbnail")
                if thumbnail:
                    cache.set(cache_key, thumbnail, timeout=60*60*24)
                    return title, thumbnail
    except Exception:
        pass
    cache.set(cache_key, "/static/no_book.png", timeout=60*60*24)
    return title, "/static/no_book.png"

async def fetch_kakao_place_image(session, place):
    cache_key = f"place_img:{place}"
    img = cache.get(cache_key)
    if img:
        return place, img

    headers = {"Authorization": f"KakaoAK {config('KAKAO_API_KEY')}"}
    search_query = f"{place} 여행지"
    params = {"query": search_query, "sort": "accuracy"}
    url = "https://dapi.kakao.com/v2/search/image"
    try:
        async with session.get(url, headers=headers, params=params, timeout=2) as response:
            data = await response.json()
            if data.get("documents"):
                for img_doc in data["documents"]:
                    if img_doc.get("width", 0) > 400 and img_doc.get("height", 0) > 300:
                        cache.set(cache_key, img_doc["image_url"], timeout=60*60*24)
                        return place, img_doc["image_url"]
                image_url = data["documents"][0].get("image_url")
                if image_url:
                    cache.set(cache_key, image_url, timeout=60*60*24)
                    return place, image_url
    except Exception:
        pass
    cache.set(cache_key, "/static/no_travel.png", timeout=60*60*24)
    return place, "/static/no_travel.png"

async def get_all_images(book_titles, place_names):
    async with aiohttp.ClientSession() as session:
        book_tasks = [fetch_kakao_book_image(session, title) for title in book_titles]
        place_tasks = [fetch_kakao_place_image(session, place) for place in place_names]
        book_results = await asyncio.gather(*book_tasks)
        place_results = await asyncio.gather(*place_tasks)
    # 딕셔너리로 변환
    book_img_dict = dict(book_results)
    place_img_dict = dict(place_results)
    return book_img_dict, place_img_dict

# --- 비동기 → 동기 Wrapper (Django Sync 뷰에서 호출) ---
def get_images_parallel(book_titles, place_names):
    try:
        return asyncio.run(get_all_images(book_titles, place_names))
    except RuntimeError:
        # 이미 이벤트 루프가 실행 중일 때 (예: Jupyter 환경 등)
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        return new_loop.run_until_complete(get_all_images(book_titles, place_names))

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
