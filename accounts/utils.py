import random
from django.core.mail import send_mail

def generate_email_code():
    return str(random.randint(100000, 999999))  # 6자리 인증번호 생성

def send_email_code(email, code):
    subject = '회원가입 이메일 인증 코드입니다.'
    message = f'인증 코드는 {code} 입니다. 다른 사람과 공유하지 마세요.'
    from_email = 'mbcaca0007@gmail.com'  # settings.py EMAIL_HOST_USER와 동일하게 설정하세요.
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
