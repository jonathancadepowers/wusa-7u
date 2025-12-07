from django.contrib import admin
from .models import Player, Team, Manager, Draft, PlayerRanking, ManagerDaughterRanking, DraftPick


@admin.register(Draft)
class DraftAdmin(admin.ModelAdmin):
    list_display = ['draft_date', 'rounds', 'picks_per_round', 'created_at']
    list_filter = ['draft_date']
    search_fields = []


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone', 'created_at', 'updated_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'manager_secret', 'created_at', 'updated_at']
    list_filter = ['manager']
    search_fields = ['name', 'manager_secret']


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'team', 'birthday', 'school', 'parent_email_1', 'attended_try_out_display', 'draftable_display']
    list_filter = ['team', 'school', 'jersey_size', 'attended_try_out', 'draftable']
    search_fields = ['first_name', 'last_name', 'parent_email_1', 'parent_email_2']
    date_hierarchy = 'birthday'

    class Media:
        js = ('admin/js/player_inline_edit.js',)

    def attended_try_out_display(self, obj):
        from django.utils.html import format_html
        checked = 'checked' if obj.attended_try_out else ''
        return format_html(
            '<input type="checkbox" class="inline-edit-checkbox" data-player-id="{}" data-field="attended_try_out" {}>',
            obj.id, checked
        )
    attended_try_out_display.short_description = 'Attended try out'

    def draftable_display(self, obj):
        from django.utils.html import format_html
        checked = 'checked' if obj.draftable else ''
        return format_html(
            '<input type="checkbox" class="inline-edit-checkbox" data-player-id="{}" data-field="draftable" {}>',
            obj.id, checked
        )
    draftable_display.short_description = 'Draftable'

    fieldsets = (
        ('Team Assignment', {
            'fields': ('team',)
        }),
        ('Player Information', {
            'fields': ('first_name', 'last_name', 'birthday', 'school', 'jersey_size', 'attended_try_out', 'draftable')
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


@admin.register(PlayerRanking)
class PlayerRankingAdmin(admin.ModelAdmin):
    list_display = ['id', 'ranking', 'created_at', 'updated_at']
    search_fields = ['ranking']


@admin.register(ManagerDaughterRanking)
class ManagerDaughterRankingAdmin(admin.ModelAdmin):
    list_display = ['id', 'manager', 'ranking', 'created_at', 'updated_at']
    search_fields = ['ranking']
    list_filter = ['manager']


@admin.register(DraftPick)
class DraftPickAdmin(admin.ModelAdmin):
    list_display = ['round', 'pick', 'team', 'player', 'created_at', 'updated_at']
    list_filter = ['round', 'team']
    search_fields = ['player__first_name', 'player__last_name', 'team__name']
