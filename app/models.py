from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    phone = models.CharField(max_length=11, unique=True)  # 手机号
    info = models.TextField(blank=True, null=True)  # 个性简介
    face = models.ImageField(upload_to='user_faces/', blank=True, null=True)
    uuid = models.CharField(max_length=255, unique=True)  # 唯一标识符
    add_time = models.DateTimeField(default=timezone.now)  # 登录时间

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'user'
        ordering = ['-add_time']
        verbose_name = '用户'
        verbose_name_plural = '用户'


class Userlog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userlogs')  # 用户ID
    ip = models.CharField(max_length=100)  # 用户IP地址
    add_time = models.DateTimeField(default=timezone.now)  # 登录时间

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'userlog'
        ordering = ['-add_time']
        verbose_name = '日志'
        verbose_name_plural = '日志'


class ScenicInfo(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    hot = models.CharField(max_length=255)
    score = models.CharField(max_length=10)
    num = models.IntegerField()
    country = models.CharField(max_length=255)
    img_url = models.CharField(max_length=255)
    comment = models.TextField(blank=True, null=True)
    detail_url = models.CharField(max_length=255)
    tel = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    detail = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'scenic_info'
        verbose_name = '景点'
        verbose_name_plural = '景点'


class Rating(models.Model):
    user_id = models.IntegerField()
    scenic = models.ForeignKey(ScenicInfo, on_delete=models.CASCADE)
    rating = models.IntegerField()

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'ratings'
        verbose_name = '评分'
        verbose_name_plural = '评分'


class Collect(models.Model):
    scenic = models.ForeignKey(ScenicInfo, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookcols')  # 所属用户
    add_time = models.DateTimeField(default=timezone.now)  # 添加时间

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'collect'
        ordering = ['-add_time']
        verbose_name = '收藏'
        verbose_name_plural = '收藏'


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')  # 用户ID
    scenic = models.ForeignKey(ScenicInfo, on_delete=models.CASCADE, related_name='comments')  # 景点ID
    content = models.TextField()  # 评论内容
    add_time = models.DateTimeField(default=timezone.now)  # 评论时间

    def __str__(self):
        return f"Comment {self.id} by {self.user.name}"

    class Meta:
        db_table = 'comment'
        ordering = ['-add_time']
        verbose_name = '评论'
        verbose_name_plural = '评论'
