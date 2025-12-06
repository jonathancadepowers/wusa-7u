from django.contrib import admin
from .models import Player, Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager_secret', 'created_at', 'updated_at']
    search_fields = ['name', 'manager_secret']


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'team', 'birthday', 'school', 'parent_email_1']
    list_filter = ['team', 'school', 'jersey_size']
    search_fields = ['first_name', 'last_name', 'parent_email_1', 'parent_email_2']
    date_hierarchy = 'birthday'

    fieldsets = (
        ('Team Assignment', {
            'fields': ('team',)
        }),
        ('Player Information', {
            'fields': ('first_name', 'last_name', 'birthday', 'school', 'jersey_size')
        }),
        ('Registration Details', {
            'fields': ('history', 'conflict', 'additional_registration_info')
        }),
        ('Parent Contact - Primary', {
            'fields': ('parent_phone_1', 'parent_email_1')
        }),
        ('Parent Contact - Secondary', {
            'fields': ('parent_phone_2', 'parent_email_2'),
            'classes': ('collapse',)
        }),
        ('Volunteers', {
            'fields': ('manager_volunteer_name', 'assistant_manager_volunteer_name'),
            'classes': ('collapse',)
        }),
    )
