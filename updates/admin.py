# Register your models here.


from django.contrib import admin
from django.utils.safestring import mark_safe

from makeaton.admin import common_exclude
from makeaton.models import TeamMember
from .models import ImParticipating, SocialMediaPosts


class ImParticipatingAdmin(admin.ModelAdmin):
    list_display = ('poster', 'is_generated', 'member')
    list_filter = ('is_generated', 'member')
    search_fields = ('member__name',)
    change_list_template = 'admin/poster_changelist.html'
    exclude = common_exclude + ['is_generated']
    readonly_fields = ('poster', 'remarks')
    poster = None

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "member" and not request.user.is_superuser:
            # Apply your specific filter to the TeamMember queryset
            kwargs["queryset"] = TeamMember.objects.filter(team__leader=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(member__team__leader=request.user)


class SocialMediaPostsAdmin(admin.ModelAdmin):
    list_display = ('title', 'link', 'verified', 'screenshot_preview',)
    list_filter = ('verified',)
    exclude = common_exclude + ['user']
    readonly_fields = ['verified']
    actions = ['verify']

    def screenshot_preview(self, obj):
        return mark_safe(f'<img src="{obj.screenshot.url}" height="100" />')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def verify(self, request, queryset):
        queryset.update(verified=True)
    # def get_action(self, action):
    #     return super().get_action(action)
    # s


admin.site.register(SocialMediaPosts, SocialMediaPostsAdmin)
admin.site.register(ImParticipating, ImParticipatingAdmin)
