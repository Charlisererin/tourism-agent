from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .models import User


class RegisterForm(UserCreationForm):
    phone = forms.CharField(
        label='手机',
        validators=[RegexValidator(r'1[3458]\d{9}', message='手机格式不正确!')],
        widget=forms.TextInput(attrs={
            'class': 'form-control input-lg',
            'placeholder': '手机'
        })
    )
    email = forms.EmailField(
        label='邮箱',
        widget=forms.EmailInput(attrs={
            'class': 'form-control input-lg',
            'placeholder': '邮箱'
        })
    )
    password1 = forms.CharField(
        label='密码',
        widget=forms.TextInput(attrs={
            'class': 'form-control input-lg',
            'placeholder': '密码'
        })
    )
    password2 = forms.CharField(
        label='确认密码',
        widget=forms.TextInput(attrs={
            'class': 'form-control input-lg',
            'placeholder': '确认密码'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control input-lg',
                'placeholder': '用户名'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control input-lg',
                'placeholder': '密码'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control input-lg',
                'placeholder': '确认密码'
            })
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('此用户名已存在!')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('此邮箱已存在!')
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if User.objects.filter(phone=phone).exists():
            raise ValidationError('此手机号已存在!')
        return phone


class LoginForm(forms.Form):
    username = forms.CharField(
        label='用户名',
        widget=forms.TextInput(attrs={
            'class': 'form-control input-lg',
            'placeholder': '用户名',
            'required': 'required'
        })
    )
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control input-lg',
            'placeholder': '密码',
            'required': 'required'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError('用户名或密码错误！')
            elif not user.is_active:
                raise forms.ValidationError('该账号已被禁用！')

        return cleaned_data


class UserDetailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'info', 'face']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'info': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        }


class PwdForm(forms.Form):
    old_pwd = forms.CharField(
        label='旧密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '旧密码',
            'required': 'required'
        })
    )
    new_pwd = forms.CharField(
        label='新密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '新密码',
            'required': 'required'
        })
    )


class StarForm(forms.Form):
    star = forms.ChoiceField(
        label='星级',
        choices=[(1, '1星'), (2, '2星'), (3, '3星'), (4, '4星'), (5, '5星')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
