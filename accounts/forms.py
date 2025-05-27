# ✅ forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import CustomUser
from django.core.exceptions import ValidationError
import re

PROFILE_CHOICES = [
    ("profile1.png", "1번 이미지"),
    ("profile2.png", "2번 이미지"),
    ("profile3.png", "3번 이미지"),
    ("profile4.png", "4번 이미지"),
    ("profile5.png", "5번 이미지"),
]

class CustomUserCreationForm(UserCreationForm):

    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'})) 

    birthday = forms.DateField(
        widget=forms.SelectDateWidget(years=range(1950, 2024)),
        required=True
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '010-1234-5678'})
    )
    profile_picture = forms.ChoiceField(
        choices=PROFILE_CHOICES,
        required=False,
        label="프로필 사진 선택"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'birthday', 'phone_number', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and not re.match(r'^010-\d{4}-\d{4}$', phone):
            raise ValidationError("전화번호는 010-1234-5678 형식으로 입력해주세요.")
        return phone


class CustomUserChangeForm(UserChangeForm):
    nickname = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '닉네임 입력'})
    )
    birthday = forms.DateField(
        widget=forms.SelectDateWidget(years=range(1950, 2024)),
        required=True
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '010-0000-0000'})
    )
    profile_picture = forms.ChoiceField(
        choices=PROFILE_CHOICES,
        required=False,
        label="프로필 사진 선택"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'nickname', 'birthday', 'phone_number', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password' in self.fields:
            self.fields.pop('password')

    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if not re.match(r'^[\w가-힣]+$', nickname):
            raise forms.ValidationError("닉네임은 한글, 영문, 숫자, 밑줄(_)만 사용할 수 있습니다.")
        if CustomUser.objects.exclude(pk=self.instance.pk).filter(nickname=nickname).exists():
            raise forms.ValidationError("이미 사용 중인 닉네임입니다.")
        return nickname

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and not re.match(r'^010-\d{4}-\d{4}$', phone):
            raise ValidationError("전화번호는 010-1234-5678 형식으로 입력해주세요.")
        return phone


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'ID'
        self.fields['password'].label = 'PASSWORD'

    error_messages = {
        'invalid_login': "올바른 사용자 이름과 비밀번호를 입력하십시오.",
        'inactive': "이 계정은 비활성화되어 있습니다.",
    }


class PasswordResetForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, label="새 비밀번호")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="비밀번호 확인")

    def clean(self):
        cleaned_data = super().clean()
        new_pw = cleaned_data.get("new_password")
        confirm_pw = cleaned_data.get("confirm_password")

        if new_pw and confirm_pw and new_pw != confirm_pw:
            raise forms.ValidationError("비밀번호와 비밀번호 확인이 일치하지 않습니다.")
        return cleaned_data
