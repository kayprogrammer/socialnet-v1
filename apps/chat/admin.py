from django import forms
from django.contrib import admin

from apps.chat.models import Chat, Message

from apps.chat.validators import validate_chat_users_m2m

# Register your models here.


class ChatForm(forms.ModelForm):
    def clean_users(self):
        users = self.cleaned_data.get("users")
        if users:
            validate_chat_users_m2m(
                users, self.cleaned_data.get("ctype"), self.cleaned_data.get("owner")
            )
        return users


class ChatAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "ctype", "created_at", "updated_at")
    list_filter = ("name", "owner", "ctype", "created_at", "updated_at")
    list_display_links = ("name", "owner")
    form = ChatForm


class MessageAdmin(admin.ModelAdmin):
    list_display = ("chat", "sender", "text", "file", "updated_at")
    list_filter = ("chat", "sender", "text", "file", "updated_at")


admin.site.register(Chat, ChatAdmin)
admin.site.register(Message, MessageAdmin)
