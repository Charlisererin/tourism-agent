from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import User, Userlog, ScenicInfo, Rating, Collect, Comment


@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('id', 'username', 'email', 'phone', 'is_staff', 'is_active', 'add_time')
    list_display_links = ('id', 'username')
    search_fields = ('username', 'email', 'phone')
    list_filter = ('is_staff', 'is_active', 'add_time')
    list_per_page = 20
    ordering = ('-add_time',)
    readonly_fields = ('add_time', 'uuid', 'last_login', 'date_joined')

    fieldsets = (
        ('账户信息', {
            'fields': ('username', 'email', 'phone', 'password')
        }),
        ('权限状态', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('其他信息', {
            'fields': ('info', 'face', 'uuid', 'add_time', 'last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    def get_list_display(self, request):
        return ['id', 'username', 'email', 'phone', 'is_staff', 'is_active', 'add_time']

    class Meta:
        verbose_name = '用户管理'
        verbose_name_plural = '用户管理'


@admin.register(Userlog)
class UserlogAdmin(ModelAdmin):
    list_display = ('id', 'user_info', 'ip', 'add_time')
    list_display_links = ('id', 'user_info')
    search_fields = ('user__username', 'ip')
    list_filter = ('add_time',)
    list_per_page = 20
    ordering = ('-add_time',)
    readonly_fields = ('add_time',)

    def user_info(self, obj):
        return f"{obj.user.username}({obj.user.phone})"

    user_info.short_description = '用户信息'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    class Meta:
        verbose_name = '用户日志'
        verbose_name_plural = '用户日志'


@admin.register(ScenicInfo)
class ScenicInfoAdmin(ModelAdmin):
    list_display = ('id', 'title', 'address', 'score', 'num', 'country', 'hot', 'tag')
    list_display_links = ('id', 'title')
    search_fields = ('title', 'address', 'country', 'tag')
    list_filter = ('country', 'score')
    list_per_page = 20
    ordering = ('-id',)
    readonly_fields = ('id',)

    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'address', 'country', 'tag')
        }),
        ('评分信息', {
            'fields': ('hot', 'score', 'num')
        }),
        ('详情信息', {
            'fields': ('img_url', 'detail_url', 'tel', 'detail'),
            'classes': ('collapse',)
        }),
        ('评论信息', {
            'fields': ('comment',),
            'classes': ('collapse',)
        }),
    )

    class Meta:
        verbose_name = '景点管理'
        verbose_name_plural = '景点管理'


@admin.register(Rating)
class RatingAdmin(ModelAdmin):
    list_display = ('id', 'user_id', 'scenic_info', 'rating')
    list_display_links = ('id', 'user_id')
    search_fields = ('scenic__title', 'user_id')
    list_filter = ('rating',)
    list_per_page = 20
    ordering = ('-id',)
    readonly_fields = ('id',)

    def scenic_info(self, obj):
        return f"{obj.scenic.title}({obj.scenic.score}分)"

    scenic_info.short_description = '景点信息'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('scenic')

    class Meta:
        verbose_name = '评分管理'
        verbose_name_plural = '评分管理'


@admin.register(Collect)
class CollectAdmin(ModelAdmin):
    list_display = ('id', 'user_info', 'scenic_info', 'add_time')
    list_display_links = ('id', 'user_info')
    search_fields = ('user__username', 'scenic__title')
    list_filter = ('add_time',)
    list_per_page = 20
    ordering = ('-add_time',)
    readonly_fields = ('add_time',)

    def user_info(self, obj):
        return f"{obj.user.username}({obj.user.phone})"

    user_info.short_description = '用户信息'

    def scenic_info(self, obj):
        return f"{obj.scenic.title}({obj.scenic.country})"

    scenic_info.short_description = '景点信息'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'scenic')

    class Meta:
        verbose_name = '收藏管理'
        verbose_name_plural = '收藏管理'


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ('id', 'user_info', 'scenic_info', 'content_short', 'add_time')
    list_display_links = ('id', 'user_info')
    search_fields = ('user__username', 'scenic__title', 'content')
    list_filter = ('add_time', 'scenic')
    list_per_page = 20
    ordering = ('-add_time',)
    readonly_fields = ('add_time',)

    def user_info(self, obj):
        return f"{obj.user.username}({obj.user.phone})"

    user_info.short_description = '用户信息'

    def scenic_info(self, obj):
        return f"{obj.scenic.title}({obj.scenic.country})"

    scenic_info.short_description = '景点信息'

    def content_short(self, obj):
        return obj.content[:30] + '...' if len(obj.content) > 30 else obj.content

    content_short.short_description = '评论内容'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'scenic')

    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'scenic')
        }),
        ('评论内容', {
            'fields': ('content', 'add_time')
        }),
    )

    class Meta:
        verbose_name = '评论管理'
        verbose_name_plural = '评论管理'


# 设置后台标题
admin.site.site_header = '旅游景点推荐系统后台管理'
admin.site.site_title = '旅游景点推荐系统后台'
