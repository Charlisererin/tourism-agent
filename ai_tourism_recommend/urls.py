"""
URL configuration for ai_tourism_recommend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.static import serve  # 上传文件处理函数

from app import views
from .settings import MEDIA_ROOT

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('<int:page>/', views.index, name='index_page'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('regist/', views.register, name='register'),
    path('user/', views.user_detail, name='user'),
    path('pwd/', views.change_pwd, name='pwd'),
    path('loginlog/<int:page>/', views.user_loginlog, name='loginlog'),
    path('collect/<int:page>/', views.user_collect, name='collect'),
    path('echarts/', views.echarts_view, name='echarts'),
    path('statics_api/', views.statics_api, name='statics_api'),
    path('recommend/', views.recommend_view, name='recommend'),
    path('collect/add/', views.collect_add, name='collect_add'),
    path('collect/del/', views.collect_del, name='collect_del'),
    path('search/<int:page>/', views.search, name='search'),
    path('play/<int:id>/', views.scenic_detail, name='play'),
    path('comment/add/', views.comment_add, name='comment_add'),
    path('comment/del/', views.comment_del, name='comment_del'),
    path('chat/', views.chat, name='chat'),
    path('api/chat/send', views.send_message, name='send_message'),
    path('api/chat/history', views.get_chat_history, name='get_chat_history'),
    path('api/chat/clear', views.clear_chat_history, name='clear_chat_history'),
    path('api/chat/sessions', views.get_user_sessions, name='get_user_sessions'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
