import asyncio
import json
import os
import uuid
from datetime import datetime
from math import sqrt

import pytz
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from pymongo import MongoClient

from .forms import RegisterForm, LoginForm, UserDetailForm, PwdForm, StarForm
from .models import Userlog, Collect, Rating, ScenicInfo, Comment
from .qianwen_client import create_client, QianwenAPIError


def change_filename(filename):
    fileinfo = filename.split('.')
    filename = datetime.now().strftime('%Y%m%d%H%M%S') + str(uuid.uuid4().hex) + '.' + fileinfo[-1]
    return filename


def index(request, page=1):
    scenic_list = ScenicInfo.objects.all().order_by('id')
    paginator = Paginator(scenic_list, 12)
    page_data = paginator.get_page(page)
    return render(request, 'index.html', {'page_data': page_data})


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                Userlog.objects.create(
                    user=user,
                    ip=request.META.get('REMOTE_ADDR')
                )
                return redirect('index')
            else:
                form.add_error(None, '用户名或密码错误')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')


def register(request):
    """
    注册
    :param request:
    :return:
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.uuid = uuid.uuid4().hex
            user.save()
            messages.success(request, '注册成功！3秒后将自动跳转到登录页面。')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'regist.html', {'form': form})


@login_required
def user_detail(request):
    user = request.user
    if request.method == 'POST':
        form = UserDetailForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            # 处理上传的文件
            if 'face' in request.FILES:
                # 确保目录存在
                os.makedirs(os.path.join(settings.MEDIA_ROOT, 'user_faces'), exist_ok=True)
                # 获取上传的文件
                uploaded_file = request.FILES['face']
                # 生成新文件名
                new_filename = change_filename(uploaded_file.name)
                # 构造完整保存路径
                file_path = os.path.join('user_faces', new_filename)
                # 保存文件
                with open(os.path.join(settings.MEDIA_ROOT, file_path), 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                # 更新用户 face 字段
                user.face = file_path
            # 保存表单
            form.save()
            messages.success(request, '保存成功！')
            return redirect('user')
    else:
        form = UserDetailForm(instance=user)
    return render(request, 'user.html', {'form': form, 'user': user})


@login_required
def change_pwd(request):
    if request.method == 'POST':
        form = PwdForm(request.POST)
        if form.is_valid():
            if check_password(form.cleaned_data['old_pwd'], request.user.password):
                request.user.set_password(form.cleaned_data['new_pwd'])
                request.user.save()
                logout(request)
                return redirect('login')
            else:
                form.add_error('old_pwd', '旧密码错误')
    else:
        form = PwdForm()
    return render(request, 'pwd.html', {'form': form})


@login_required
def user_loginlog(request, page=1):
    logs = Userlog.objects.filter(user=request.user).order_by('-add_time')
    paginator = Paginator(logs, 10)
    page_data = paginator.get_page(page)
    return render(request, 'loginlog.html', {'page_obj': page_data})


@login_required
def user_collect(request, page=1):
    collects = Collect.objects.filter(user=request.user).select_related('scenic')
    scenic_ids = [c.scenic_id for c in collects]
    scenic_list = ScenicInfo.objects.filter(id__in=scenic_ids).order_by('id')

    paginator = Paginator(scenic_list, 10)
    page_data = paginator.get_page(page)
    return render(request, 'collect.html', {'page_data': page_data})


@login_required
def echarts_view(request):
    return render(request, 'echarts.html')


@login_required
def statics_api(request):
    collects = Collect.objects.filter(user=request.user).values('scenic__country').annotate(
        count=Count('scenic__country')).order_by('-count')[:10]
    data = [{'value': item['count'], 'name': item['scenic__country']} for item in collects]
    return JsonResponse({'data': data})


@login_required
def recommend_view(request):
    user_ratings = Rating.objects.filter(user_id=request.user.id)
    if user_ratings.exists():
        try:
            result_dict = {}
            data = Rating.objects.all()
            for entry in data:
                if entry.user_id not in result_dict:
                    result_dict[entry.user_id] = {}
                result_dict[entry.user_id][entry.scenic_id] = int(entry.rating)
            user_id = request.user.id
            scenic_id_list = []
            r = Recommender(result_dict)
            k = r.recommend(user_id)
            for i in range(len(k)):
                scenic_id_list.append(k[i][0])
            route = []
            for per_id in scenic_id_list:
                data = ScenicInfo.objects.filter(id=per_id).first()
                route.append(data.title)
        except Exception as e:
            print(e)
            route = [scenic.title for scenic in ScenicInfo.objects.order_by('-hot')[:5]]
    else:
        route = [scenic.title for scenic in ScenicInfo.objects.order_by('-hot')[:5]]
    return render(request, 'recommend.html', {'spot_name': route})


@login_required
@require_GET
def collect_add(request):
    scenic_id = request.GET.get("mid")
    if Collect.objects.filter(scenic_id=scenic_id, user=request.user).exists():
        return JsonResponse({'ok': 0})
    Collect.objects.create(scenic_id=scenic_id, user=request.user)
    return JsonResponse({'ok': 1})


@login_required
@require_GET
def collect_del(request):
    scenic_id = request.GET.get("mid")
    Collect.objects.filter(scenic_id=scenic_id, user=request.user).delete()
    return JsonResponse({'ok': 1})


def search(request, page=1):
    key = request.GET.get('key', '')
    scenic_list = ScenicInfo.objects.filter(title__icontains=key).order_by('id')
    paginator = Paginator(scenic_list, 10)
    page_data = paginator.get_page(page)
    count = scenic_list.count()
    return render(request, 'search.html', {
        'key': key,
        'page_data': page_data,
        'count': count
    })


def scenic_detail(request, id):
    scenic = get_object_or_404(ScenicInfo, id=id)
    if request.user.is_authenticated:
        form = StarForm(request.POST)
        if form.is_valid():
            Rating.objects.update_or_create(
                user_id=request.user.id,
                scenic=scenic,
                defaults={'rating': form.cleaned_data['star']}
            )
    else:
        form = StarForm()

    if request.user.is_authenticated:
        rating = Rating.objects.filter(scenic=scenic, user_id=request.user.id).first()
        scenic.star = rating.rating if rating else 0
    else:
        scenic.star = 0
    full_stars = range(scenic.star)
    empty_stars = range(5 - scenic.star)
    comments = Comment.objects.filter(scenic=scenic).order_by('-add_time')
    return render(request, 'play.html', {
        'scenic': scenic,
        'comments': comments,
        'form': form,
        'full_stars': full_stars,
        'empty_stars': empty_stars,
    })


class Recommender:
    # data：数据集，这里指users
    # k：表示得出最相近的k的近邻
    # metric：表示使用计算相似度的方法
    # n：表示推荐景点的个数
    def __init__(self, data, k=3, metric='pearson', n=5):

        self.k = k
        self.n = n
        self.user_id = {}
        self.user_id_name = {}
        self.product_id_name = {}

        self.metric = metric
        if self.metric == 'pearson':
            self.fn = self.pearson
        if type(data).__name__ == 'dict':
            self.data = data

    def convert_product_id_name(self, id):
        if id in self.product_id_name:
            return self.product_id_name[id]
        else:
            return id

    # 定义的计算相似度的公式，用的是皮尔逊相关系数计算方法
    def pearson(self, rating1, rating2):
        sum_xy = 0
        sum_x = 0
        sum_y = 0
        sum_x2 = 0
        sum_y2 = 0
        n = 0
        for key in rating1:
            if key in rating2:
                n += 1
                x = rating1[key]
                y = rating2[key]
                sum_xy += x * y
                sum_x += x
                sum_y += y
                sum_x2 += pow(x, 2)
                sum_y2 += pow(y, 2)
        if n == 0:
            return 0

        # 皮尔逊相关系数计算公式
        denominator = sqrt(sum_x2 - pow(sum_x, 2) / n) * sqrt(sum_y2 - pow(sum_y, 2) / n)
        if denominator == 0:
            return 0
        else:
            return (sum_xy - (sum_x * sum_y) / n) / denominator

    def compute_nearest_neighbor(self, username):
        distances = []
        for instance in self.data:
            if instance != username:
                distance = self.fn(self.data[username], self.data[instance])
                distances.append((instance, distance))

        distances.sort(key=lambda list_tuple: list_tuple[1], reverse=True)
        return distances

    # 推荐算法的主体函数
    def recommend(self, user):
        # 定义一个字典，用来存储推荐的景点和分数
        recommendations = {}
        # 计算出user与所有其他用户的相似度，返回一个list
        nearest = self.compute_nearest_neighbor(user)
        user_ratings = self.data[user]
        total_distance = 0.0
        # 得住最近的k个近邻的总距离
        for i in range(self.k):
            total_distance += nearest[i][1]
        if total_distance == 0.0:
            total_distance = 1.0

        # 将与user最相近的k个人中user没有打分景点推荐给user，并且这里又做了一个分数的计算排名
        for i in range(self.k):
            # 第i个人的与user的相似度，转换到[0,1]之间
            weight = nearest[i][1] / total_distance
            # 第i个人的name
            name = nearest[i][0]
            # 第i个用户看过的书和相应的打分
            neighbor_ratings = self.data[name]
            for artist in neighbor_ratings:
                if not artist in user_ratings:
                    if artist not in recommendations:
                        recommendations[artist] = (neighbor_ratings[artist] * weight)
                    else:
                        recommendations[artist] = (recommendations[artist] + neighbor_ratings[artist] * weight)
        recommendations = list(recommendations.items())
        recommendations = [(self.convert_product_id_name(k), v) for (k, v) in recommendations]
        # 做了一个排序
        recommendations.sort(key=lambda list_tuple: list_tuple[1], reverse=True)
        return recommendations[:self.n]


@login_required
@require_POST
def comment_add(request):
    scenic_id = request.POST.get('scenic_id')
    content = request.POST.get('content')

    if not content:
        return JsonResponse({'status': 'error', 'msg': '评论内容不能为空'})

    scenic = get_object_or_404(ScenicInfo, id=scenic_id)
    Comment.objects.create(
        user=request.user,
        scenic=scenic,
        content=content
    )
    return JsonResponse({'status': 'success', 'msg': '评论成功'})


@login_required
@require_POST
def comment_del(request):
    comment_id = request.POST.get('comment_id')
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    comment.delete()
    return JsonResponse({'status': 'success', 'msg': '删除成功'})


def chat(request):
    return render(request, 'chat.html')


class ChatSessionManager:
    """聊天会话管理器"""
    _sessions = {}

    @classmethod
    def get_session(cls, session_id, user_id):
        """获取或创建会话"""
        if session_id not in cls._sessions:
            cls._sessions[session_id] = {
                'user_id': user_id,
                'created_at': datetime.now(),
                'messages': [],
                'client': None
            }
        return cls._sessions[session_id]

    @classmethod
    def cleanup_session(cls, session_id):
        """清理会话"""
        if session_id in cls._sessions:
            cls._sessions.pop(session_id, None)


@login_required
@require_POST
def send_message(request):
    """发送消息接口 - 同步版本"""
    try:
        # 获取请求数据
        if request.FILES:
            # 处理文件上传
            file = request.FILES.get('file')
            message = request.POST.get('message', '')
            session_id = request.POST.get('session_id', '')
            user_id = request.user.id  # 从登录用户获取
        else:
            data = request.POST
            message = data.get('message')
            session_id = data.get('session_id')
            user_id = request.user.id
            file = None

        # 获取或创建会话
        session = ChatSessionManager.get_session(session_id, str(user_id))

        # 处理文件上传
        file_path = None
        file_type = None
        if file:
            # 保存上传的文件
            file_ext = os.path.splitext(file.name)[1]
            filename = f"uploads/{uuid.uuid4()}{file_ext}"
            file_path = default_storage.save(filename, file)
            file_path = os.path.join(settings.MEDIA_ROOT, file_path)
            file_type = file.content_type

        # 调用千问API
        response_data = process_message_with_qianwen(
            session, message, file_path, file_type, str(user_id), session_id
        )

        return JsonResponse(response_data)

    except Exception as e:
        import traceback
        print(f"错误信息: {str(e)}")
        print(f"错误追踪: {traceback.format_exc()}")
        return JsonResponse({'error': str(e), 'success': False}, status=500)


def process_message_with_qianwen(session, message, file_path=None, file_type=None, user_id=None, session_id=None):
    """处理消息并调用千问API - 同步版本"""
    try:
        # 初始化客户端（如果尚未初始化）
        if not session.get('client'):
            client = create_client()
            client.initialize()
            session['client'] = client
            session['chat_instance'] = client.chat(
                user_id=user_id,
                session_id=session_id
            )

        chat_instance = session['chat_instance']

        # 根据文件类型选择不同的处理方式
        if file_path:
            if file_type and file_type.startswith('image/'):
                # 图像识别
                response = chat_instance.model("qwen-vl-plus").image(
                    message or "请描述这张图片",
                    file_path
                )
            elif file_type and file_type.startswith('video/'):
                # 视频识别（简化处理，使用第一帧）
                response = chat_instance.model("qwen-vl-plus").image(
                    message or "请描述这个视频",
                    file_path
                )
            else:
                # 普通文件（作为文本处理）
                # 这里可以添加文件内容读取逻辑
                response = chat_instance.ask(f"文件: {file_path}\n\n用户消息: {message}")
        else:
            # 纯文本对话
            response = chat_instance.ask(message)

        # 提取AI回复
        ai_response = response['choices'][0]['message']['content']

        # 保存到会话历史
        user_message = {
            'type': 'user',
            'content': message,
            'file_path': file_path,
            'timestamp': datetime.now().isoformat()
        }
        ai_message = {
            'type': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now().isoformat()
        }

        if 'messages' not in session:
            session['messages'] = []

        session['messages'].extend([user_message, ai_message])

        # 限制历史消息数量（防止内存溢出）
        if len(session['messages']) > 20:
            session['messages'] = session['messages'][-20:]

        return {
            'success': True,
            'user_message': message,
            'ai_response': ai_response,
            'has_file': bool(file_path),
            'file_type': file_type,
            'session_id': session_id
        }

    except QianwenAPIError as e:
        # 清理无效的客户端
        if session.get('client'):
            try:
                session['client'].close()
            except:
                pass
            session['client'] = None
            session['chat_instance'] = None

        raise e
    except Exception as e:
        # 清理无效的客户端
        if session.get('client'):
            try:
                session['client'].close()
            except:
                pass
            session['client'] = None
            session['chat_instance'] = None

        raise e


@login_required
@require_POST
def clear_chat_history(request):
    """清空聊天历史"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        user_id = str(request.user.id)

        # 从MongoDB删除该会话的所有消息
        collection = get_chat_collection()
        collection.delete_many({
            "user_id": user_id,
            "session_id": session_id
        })

        if session_id and session_id in ChatSessionManager._sessions:
            session = ChatSessionManager._sessions[session_id]
            session['messages'] = []

            # 重新初始化聊天实例以清除模型记忆
            if session.get('client'):
                asyncio.run(session['client'].close())
                session['client'] = None
                session['chat_instance'] = None

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_mongo_client():
    return MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))


def get_chat_db():
    """获取聊天数据库"""
    client = get_mongo_client()
    # 指定数据库名称
    db_name = getattr(settings, 'MONGO_DB_NAME', 'qianwen_memory')
    return client[db_name]


def get_chat_collection():
    """获取聊天消息集合"""
    db = get_chat_db()
    # 指定集合名称
    collection_name = getattr(settings, 'MONGO_CHAT_COLLECTION', 'conversations')
    return db[collection_name]


@login_required
@require_GET
def get_user_sessions(request):
    """获取用户的所有会话列表"""
    try:
        user_id = str(request.user.id)
        collection = get_chat_collection()

        # 获取用户的所有唯一会话ID
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$session_id",
                "last_message_time": {"$max": "$timestamp"},
                "message_count": {"$sum": 1},
                "first_user_message": {
                    "$first": {
                        "$cond": [
                            {"$eq": ["$role", "user"]},
                            "$content",
                            None
                        ]
                    }
                }
            }},
            {"$sort": {"last_message_time": -1}},
            {"$limit": 50}
        ]

        sessions_result = list(collection.aggregate(pipeline))

        # 格式化会话列表
        session_list = []
        for session in sessions_result:
            # 获取会话的最后一条消息作为预览
            last_message = collection.find_one(
                {"user_id": user_id, "session_id": session["_id"]},
                sort=[("timestamp", -1)]
            )

            # 使用第一条用户消息作为标题，如果没有则使用默认标题
            session_title = session.get("first_user_message", "新会话")
            if session_title and len(session_title) > 20:
                session_title = session_title[:20] + "..."

            utc_time = session['last_message_time']
            # 转换为中国时间
            utc_time = utc_time.replace(tzinfo=pytz.UTC)  # 设置为UTC时区
            china_time = utc_time.astimezone(pytz.timezone('Asia/Shanghai'))
            session_list.append({
                "session_id": session["_id"],
                "title": session_title or "新会话",
                "lastActive": china_time,
                "message_count": session["message_count"],
                "preview": last_message["content"][:50] + "..." if last_message else "暂无消息"
            })

        return JsonResponse({
            'success': True,
            'sessions': session_list
        })

    except Exception as e:
        import traceback
        print(f"Error in get_user_sessions: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def get_chat_history(request):
    """获取特定会话的聊天历史"""
    try:
        session_id = request.GET.get('session_id')
        user_id = str(request.user.id)

        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'session_id is required'
            }, status=400)

        collection = get_chat_collection()

        # 从MongoDB查询该会话的所有消息，按_id升序排序
        messages_cursor = collection.find({
            "user_id": user_id,
            "session_id": session_id
        }).sort("_id", 1)  # 改为按_id升序排序

        messages = []
        for msg in messages_cursor:
            utc_time = msg['timestamp']
            # 转换为中国时间
            utc_time = utc_time.replace(tzinfo=pytz.UTC)  # 设置为UTC时区
            china_time = utc_time.astimezone(pytz.timezone('Asia/Shanghai'))
            messages.append({
                'type': msg['role'],  # user 或 assistant
                'content': msg['content'],
                'timestamp': china_time,
                'file_path': msg.get('file_path')
            })

        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'messages': messages
        })

    except Exception as e:
        import traceback
        print(f"Error in get_chat_history: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
