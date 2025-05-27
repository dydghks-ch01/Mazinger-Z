from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from .models import CustomUser
from django.contrib import messages # 아이디찾기
from django.contrib.auth import get_user_model # 비밀번호찾기
from django.http import HttpResponse # 비밀번호찾기
from django.contrib.auth.hashers import make_password # 비밀번호 재설정
from .forms import PasswordResetForm
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from urllib.parse import urlencode
from django.views.decorators.csrf import csrf_exempt
import json
from lyricsgen.models import GeneratedLyrics
from .utils import generate_email_code, send_email_code

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST,request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 회원가입 후 바로 로그인
            return redirect('main')
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})


# 로그인뷰
def login_view(request):
    next_url = request.POST.get('next') or request.GET.get('next')  # ✅ GET도 체크

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(next_url or 'main')  # ✅ next가 있으면 그곳으로 이동
    else:
        form = CustomAuthenticationForm()

    return render(request, 'login.html', {'form': form, 'next': next_url})

# 로그아웃 뷰
def logout_view(request):
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or 'main'
    logout(request)
    return redirect(next_url)

def check_nickname(request):
    nickname = request.GET.get('nickname')
    current_user_id = request.user.id
    exists = CustomUser.objects.exclude(pk=current_user_id).filter(nickname=nickname).exists()
    return JsonResponse({'duplicate': exists})

# 아이디찾기
def find_username(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        user = CustomUser.objects.filter(phone_number=phone).first()
        if user:
            return render(request, 'found_username.html', {'username': user.username})
        else:
            messages.error(request, '일치하는 사용자가 없습니다.')
    return render(request, 'find_username.html')

# 비밀번호찾기
def find_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        phone = request.POST.get('phone_number')
        try:
            user = CustomUser.objects.get(username=username, phone_number=phone)
            return redirect('reset_password', uid=user.username)
        except CustomUser.DoesNotExist:
            messages.error(request, '일치하는 사용자 정보가 없습니다.')
    return render(request, 'find_password.html')

def reset_password(request, uid):
    try:
        user = CustomUser.objects.get(username=uid)
    except CustomUser.DoesNotExist:
        messages.error(request, '유효하지 않은 접근입니다.')
        return redirect('find_password')

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            new_pw = form.cleaned_data['new_password']
            user.password = make_password(new_pw)
            user.save()
            messages.success(request, '비밀번호가 재설정되었습니다.')
            return redirect('login')
        else:
            messages.error(request, '비밀번호가 일치하지 않습니다.')  # ❗ 안내문구
    else:
        form = PasswordResetForm()

    return render(request, 'reset_password.html', {'form': form, 'username': uid})

User = get_user_model()

def check_username(request):
    username = request.GET.get("username", "")
    exists = User.objects.filter(username=username).exists()  # ✅ 정확히 일치하는지만 검사
    return JsonResponse({'available': not exists})


@csrf_exempt
def delete_lyrics(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            if not ids:
                return JsonResponse({'success': False, 'error': 'No IDs provided'})

            GeneratedLyrics.objects.filter(id__in=ids).delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=400)

# 인증번호 발송
@csrf_exempt
def send_verification_code(request):
    if request.method == "POST":
        email = request.POST.get('email')
        if not email:
            return JsonResponse({'success': False, 'error': '이메일을 입력하세요.'})
        code = generate_email_code()
        request.session['email_verification_code'] = code
        request.session['email_for_verification'] = email
        send_email_code(email, code)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'})

# 인증번호 검증
@csrf_exempt
def verify_email_code(request):
    if request.method == "POST":
        input_code = request.POST.get('code')
        saved_code = request.session.get('email_verification_code')
        if input_code == saved_code:
            return JsonResponse({'verified': True})
        else:
            return JsonResponse({'verified': False})
    return JsonResponse({'verified': False, 'error': '잘못된 요청입니다.'})

# 회원가입 최종 처리 시 이메일 인증 확인
def signup_view(request):
    if request.method == 'POST':
        if not request.session.get('email_verification_code'):
            messages.error(request, '이메일 인증을 완료해주세요.')
            form = CustomUserCreationForm(request.POST, request.FILES)
            return render(request, 'signup.html', {'form': form})

        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('main')
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

