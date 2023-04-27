from django.contrib import admin
from .models import Post, Group


class PostAdmin(admin.ModelAdmin):
    '''Customize display options "Post model".'''
    list_display = ('pk', 'text', 'pub_date', 'author', 'group',)
    list_editable = ('group', )
    search_fields = ('text', )
    list_filter = ('pub_date', )
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    '''Customize options "Group model".'''
    prepopulated_fields = {"slug": ("title",)}


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
