from django.contrib import admin
from .models import Player, Team, Manager, Draft, PlayerRanking, ManagerDaughterRanking, SiblingRanking, DraftPick, TeamPreference, PracticeSlot, PracticeSlotRanking, GeneralSetting, ValidationCode, StarredDraftPick, DivisionValidationRegistry, Event, EventType


@admin.register(Draft)
class DraftAdmin(admin.ModelAdmin):
    list_display = ['rounds_draftable', 'rounds_nondraftable', 'picks_per_round', 'created_at']
    list_filter = ['created_at']
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
    filter_horizontal = ['siblings']

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
        ('Family Relationships', {
            'fields': ('siblings', 'requests_separate_team_from_sibling')
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


@admin.register(SiblingRanking)
class SiblingRankingAdmin(admin.ModelAdmin):
    list_display = ['id', 'manager', 'ranking', 'created_at', 'updated_at']
    search_fields = ['ranking']
    list_filter = ['manager']


@admin.register(DraftPick)
class DraftPickAdmin(admin.ModelAdmin):
    list_display = ['round', 'pick', 'team', 'player', 'created_at', 'updated_at']
    list_filter = ['round', 'team']
    search_fields = ['player__first_name', 'player__last_name', 'team__name']


@admin.register(TeamPreference)
class TeamPreferenceAdmin(admin.ModelAdmin):
    list_display = ['id', 'manager', 'created_at', 'updated_at']
    list_filter = ['manager']
    search_fields = ['manager__first_name', 'manager__last_name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Manager', {
            'fields': ('manager',)
        }),
        ('Preferences', {
            'fields': ('preferences',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PracticeSlot)
class PracticeSlotAdmin(admin.ModelAdmin):
    list_display = ['id', 'practice_slot', 'get_assigned_team', 'created_at', 'updated_at']
    search_fields = ['practice_slot']
    readonly_fields = ['created_at', 'updated_at', 'get_assigned_team']

    fieldsets = (
        ('Practice Slot', {
            'fields': ('practice_slot', 'get_assigned_team')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_assigned_team(self, obj):
        """Display which team is assigned to this practice slot"""
        teams = obj.teams.all()
        if teams.exists():
            return ', '.join([team.name for team in teams])
        return 'Not assigned'
    get_assigned_team.short_description = 'Assigned Team'


@admin.register(PracticeSlotRanking)
class PracticeSlotRankingAdmin(admin.ModelAdmin):
    list_display = ['id', 'team', 'created_at', 'updated_at']
    list_filter = ['team']
    search_fields = ['team__name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Practice Slot Ranking', {
            'fields': ('team', 'rankings')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GeneralSetting)
class GeneralSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'created_at', 'updated_at']
    search_fields = ['key', 'value']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Setting', {
            'fields': ('key', 'value')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ValidationCode)
class ValidationCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'value', 'error_message', 'created_at', 'updated_at']
    search_fields = ['code', 'value', 'error_message']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Validation Code', {
            'fields': ('code', 'value', 'error_message')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StarredDraftPick)
class StarredDraftPickAdmin(admin.ModelAdmin):
    list_display = ['id', 'team', 'player', 'created_at', 'updated_at']
    list_filter = ['team']
    search_fields = ['team__name', 'player__first_name', 'player__last_name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Starred Pick', {
            'fields': ('team', 'player')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DivisionValidationRegistry)
class DivisionValidationRegistryAdmin(admin.ModelAdmin):
    list_display = ['id', 'page', 'validations_to_run_on_page_load', 'validation_code_triggers', 'created_at', 'updated_at']
    search_fields = ['page']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Validation Registry', {
            'fields': ('page', 'validations_to_run_on_page_load', 'validation_code_triggers')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'bootstrap_icon_id', 'color', 'created_at', 'updated_at']
    search_fields = ['name', 'bootstrap_icon_id']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Event Type', {
            'fields': ('name', 'bootstrap_icon_id', 'color')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'event_type', 'location', 'timestamp', 'created_at', 'updated_at']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['name', 'description', 'location']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Event Information', {
            'fields': ('name', 'event_type', 'location', 'timestamp', 'description')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
