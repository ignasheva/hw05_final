from django.contrib import admin
from .models import Post, Group, Comment, Follow


class PostAdmin(admin.ModelAdmin):
    '''Настроить параметры отображения "Модель поста".'''
    list_display = ('pk', 'text', 'pub_date', 'author', 'group',)
    list_editable = ('group', )
    search_fields = ('text', )
    list_filter = ('pub_date', )
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    '''Настроить параметры отображения "Модель группы".'''
    prepopulated_fields = {"slug": ("title",)}


class CommentAdmin(admin.ModelAdmin):
    '''Настроить параметры отображения "Модель комментария".'''
    list_display = ('pk', 'author', 'text', 'pub_date',)
    search_fields = ('author', 'text', 'pub_date',)
    list_filter = ('author',)
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    '''Настроить параметры отображения "Модель подписки".'''
    list_display = ('pk', 'user', 'author',)
    search_fields = ('user', 'author',)
    list_filter = ('user', 'author',)
    empty_value_display = 'нет подписчиков/подписок'


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
