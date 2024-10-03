from django.contrib import admin

# Register your models here.


from django.contrib import admin
from .models import IdCard, ImParticipating
from makeaton.admin import common_exclude


class PosterAdmin(admin.ModelAdmin):
    list_display = ('poster', 'is_generated', 'member')
    list_filter = ('is_generated', 'member')
    search_fields = ('member__name',)
    change_list_template = 'admin/poster_changelist.html'
    exclude = common_exclude

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('member')  # Optimize the query


admin.site.register(IdCard, PosterAdmin)
admin.site.register(ImParticipating, PosterAdmin)
