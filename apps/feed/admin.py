from django.contrib import admin
from apps.feed.models import Comment, Post, Reaction, Reply


class ReactionAdmin(admin.ModelAdmin):
    list_display = ("user", "rtype")
    list_filter = ("user", "rtype")


class PostAdmin(admin.ModelAdmin):
    list_display = ("author", "slug", "created_at", "updated_at")
    list_filter = ("author", "slug", "created_at", "updated_at")


class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "created_at", "updated_at")
    list_filter = ("author", "created_at", "updated_at")


class ReplyAdmin(admin.ModelAdmin):
    list_display = ("author", "created_at", "updated_at")
    list_filter = ("author", "created_at", "updated_at")


admin.site.register(Reaction, ReactionAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Reply, ReplyAdmin)
