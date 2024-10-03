from django import forms
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.html import format_html

from makeaton.models import Team
from .models import RSVP


class RSVPForm(forms.ModelForm):
    class Meta:
        model = RSVP
        fields = ['confirmed', 'id_cards_generated', 'posters_generated']
        widgets = {
            'confirmed': forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
        }


class RSVPAdmin(admin.ModelAdmin):
    change_list_template = "admin/rsvp_change_list.html"
    list_display = ('team', 'confirmed', 'id_cards_generated', 'posters_generated')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_site.admin_view(self.rsvp_view), name='rsvp_changelist'),
        ]
        return custom_urls + urls

    def rsvp_view(self, request):
        team = Team.objects.filter(leader=request.user).first()

        if not team:
            return render(request, 'admin/rsvp_no_team.html', {'message': "You are not associated with any team."})

        rsvp = RSVP.objects.filter(team=team).first()

        if request.method == 'POST' and not rsvp:
            form = RSVPForm(request.POST)
            if form.is_valid():
                rsvp = form.save(commit=False)
                rsvp.team = team
                rsvp.save()
                return redirect('admin:rsvp_rsvp_changelist')
        else:
            form = RSVPForm()

        context = {
            'title': 'RSVP Form',
            'form': form,
            'team': team,
            'rsvp': rsvp,
            'instructions': [
                "Please confirm your participation.",
                "Make sure to generate ID cards and posters before the deadline.",
                "This RSVP is a one-time submission."
            ],
        }
        return render(request, 'admin/rsvp_change_list.html', context)


admin.site.register(RSVP, RSVPAdmin)
