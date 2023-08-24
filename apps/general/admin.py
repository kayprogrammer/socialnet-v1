from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from apps.general.models import SiteDetail


class SiteDetailAdmin(admin.ModelAdmin):
    fieldsets = (
        ("General", {"fields": ["name", "email", "phone", "address"]}),
        ("Social", {"fields": ["fb", "tw", "wh", "ig"]}),
    )

    def has_add_permission(self, request):
        return (
            False
            if self.model.objects.count() > 0
            else super().has_add_permission(request)
        )

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.objects.all()[0]
        return HttpResponseRedirect(
            reverse(
                "admin:%s_%s_change"
                % (self.model._meta.app_label, self.model._meta.model_name),
                args=(obj.id,),
            )
        )


admin.site.register(SiteDetail, SiteDetailAdmin)
