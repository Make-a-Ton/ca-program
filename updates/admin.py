from django.contrib import admin

# Register your models here.


from django.contrib import admin
from django.db.models import Q
from makeaton.models import TeamMember
from .models import IdCard, ImParticipating, Poster
from makeaton.admin import common_exclude
from .services.poster import PosterTemplate


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
            kwargs["queryset"] = TeamMember.objects.filter(Q(imparticipating__isnull=True) | Q(imparticipating__deleted=False),team__leader=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(member__team__leader=request.user)


admin.site.register(ImParticipating, ImParticipatingAdmin)
