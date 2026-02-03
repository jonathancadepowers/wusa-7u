from django.db import models


class Draft(models.Model):
    rounds_draftable = models.IntegerField()
    rounds_nondraftable = models.IntegerField(default=0)
    picks_per_round = models.IntegerField()
    order = models.TextField()
    final_round_draft_order = models.TextField(blank=True, null=True)
    final_round_picks = models.IntegerField(null=True, blank=True)  # Number of picks in the final round

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'draft'
        ordering = ['-created_at']

    def __str__(self):
        return f"Draft {self.created_at.strftime('%Y-%m-%d')}"


class DraftPick(models.Model):
    round = models.IntegerField()
    pick = models.IntegerField()
    player = models.ForeignKey('Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='draft_picks')
    team = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='draft_picks')
    player_assigned_to_team = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'draft_picks'
        ordering = ['round', 'pick']

    def __str__(self):
        return f"Round {self.round}, Pick {self.pick}"


class Manager(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    daughter = models.ForeignKey('Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='manager_parent')
    passed_background_check = models.BooleanField(default=False)
    background_check_clearance_date = models.DateField(null=True, blank=True)
    board_member = models.BooleanField(default=False)
    comments = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'managers'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def has_valid_background_check(self):
        """Check if manager has a valid background check (passed and less than 1 year old)"""
        from datetime import date, timedelta
        if not self.passed_background_check or not self.background_check_clearance_date:
            return False
        one_year_ago = date.today() - timedelta(days=365)
        return self.background_check_clearance_date >= one_year_ago


class Team(models.Model):
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, blank=True, related_name='teams')
    name = models.CharField(max_length=100)
    manager_secret = models.CharField(max_length=100, unique=True)
    practice_slot = models.ForeignKey('PracticeSlot', on_delete=models.SET_NULL, null=True, blank=True, related_name='teams')
    preseason_practice_slot = models.TextField(blank=True, null=True)
    colors = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teams'
        ordering = ['name']

    def __str__(self):
        return self.name


class Player(models.Model):
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='players')
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    birthday = models.DateField(blank=True, null=True)
    history = models.TextField(blank=True, null=True)
    school = models.CharField(max_length=200, blank=True, null=True)
    conflict = models.TextField(blank=True, null=True)
    additional_registration_info = models.TextField(blank=True, null=True)
    parent_phone_1 = models.CharField(max_length=20)
    parent_email_1 = models.EmailField()
    parent_phone_2 = models.CharField(max_length=20, blank=True, null=True)
    parent_email_2 = models.EmailField(blank=True, null=True)
    jersey_size = models.CharField(max_length=50, blank=True, null=True)
    manager_volunteer_name = models.CharField(max_length=100, blank=True, null=True)
    assistant_manager_volunteer_name = models.CharField(max_length=100, blank=True, null=True)
    attended_try_out = models.BooleanField(default=False)
    draftable = models.BooleanField(default=True)
    siblings = models.ManyToManyField('self', blank=True, symmetrical=True)
    requests_separate_team_from_sibling = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'players'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class PlayerRanking(models.Model):
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, blank=True, related_name='rankings')
    ranking = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'player_rankings'

    def __str__(self):
        return f"Ranking {self.id} by {self.manager}" if self.manager else f"Ranking {self.id}"


class ManagerDaughterRanking(models.Model):
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, blank=True, related_name='daughter_rankings')
    ranking = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'manager_daughter_rankings'

    def __str__(self):
        return f"Manager Daughter Ranking {self.id} by {self.manager}" if self.manager else f"Manager Daughter Ranking {self.id}"


class SiblingRanking(models.Model):
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, blank=True, related_name='sibling_rankings')
    ranking = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sibling_rankings'

    def __str__(self):
        return f"Sibling Ranking {self.id} by {self.manager}" if self.manager else f"Sibling Ranking {self.id}"


class TeamPreference(models.Model):
    manager = models.ForeignKey(Manager, on_delete=models.CASCADE, related_name='team_preferences')
    preferences = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'team_preferences'

    def __str__(self):
        return f"Team Preferences for {self.manager}" if self.manager else f"Team Preferences {self.id}"


class PracticeSlot(models.Model):
    practice_slot = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'practice_slots'
        verbose_name = 'Practice Slot'
        verbose_name_plural = 'Practice Slots'

    def __str__(self):
        return self.practice_slot


class PracticeSlotRanking(models.Model):
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='practice_slot_rankings')
    rankings = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'practice_slot_rankings'
        verbose_name = 'Practice Slot Ranking'
        verbose_name_plural = 'Practice Slot Rankings'

    def __str__(self):
        return f"Practice Slot Rankings for {self.team}" if self.team else f"Practice Slot Rankings {self.id}"


class GeneralSetting(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'general_settings'
        verbose_name = 'General Setting'
        verbose_name_plural = 'General Settings'

    def __str__(self):
        return f"{self.key}: {self.value}"


class ValidationCode(models.Model):
    code = models.CharField(max_length=255, unique=True)
    value = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'validation_codes'
        verbose_name = 'Validation Code'
        verbose_name_plural = 'Validation Codes'

    def __str__(self):
        return f"{self.code}: {self.value}"


class StarredDraftPick(models.Model):
    player = models.ForeignKey('Player', on_delete=models.CASCADE, related_name='starred_by_teams')
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='starred_players')
    order = models.IntegerField(default=0)  # Order within the team's starred list
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'starred_draft_picks'
        unique_together = ('player', 'team')
        ordering = ['team', 'order']  # Order by team first, then by order
        verbose_name = 'Starred Draft Pick'
        verbose_name_plural = 'Starred Draft Picks'

    def __str__(self):
        return f"{self.team} starred {self.player}"


class DivisionValidationRegistry(models.Model):
    page = models.TextField()
    validations_to_run_on_page_load = models.JSONField(default=list)  # Renamed from required_validations
    validation_code_triggers = models.JSONField(default=list)  # New field

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'division_validation_registry'
        verbose_name = 'Division Validation Registry'
        verbose_name_plural = 'Division Validation Registry'

    def __str__(self):
        return f"Validation Registry for {self.page}"


class EventType(models.Model):
    name = models.CharField(max_length=100)
    bootstrap_icon_id = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#0d6efd', help_text='Hex color code (e.g., #0d6efd)')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'event_types'
        ordering = ['name']
        verbose_name = 'Event Type'
        verbose_name_plural = 'Event Types'

    def __str__(self):
        return self.name


class Event(models.Model):
    event_type = models.ForeignKey(EventType, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    home_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='home_events')
    away_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='away_events')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    timestamp = models.DateTimeField()
    end_date = models.DateField(blank=True, null=True)  # For multi-day events

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'events'
        ordering = ['-timestamp']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        type_name = self.event_type.name if self.event_type else 'No Type'
        return f"{self.name} ({type_name}) - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class QuickLink(models.Model):
    name = models.CharField(max_length=200)
    url = models.CharField(max_length=500)
    icon = models.CharField(max_length=100)  # Bootstrap icon class (e.g., "bi-clipboard-check")
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_fixed = models.BooleanField(default=False)  # Fixed links can't be deleted/edited and have fixed positions

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quick_links'
        ordering = ['display_order', 'name']
        verbose_name = 'Quick Link'
        verbose_name_plural = 'Quick Links'

    def __str__(self):
        return self.name


class BackgroundCheck(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    player = models.ForeignKey('Player', on_delete=models.CASCADE, related_name='background_checks')
    clearance_date = models.DateField()
    comments = models.TextField(blank=True, null=True)
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='background_checks')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'background_checks'
        ordering = ['last_name', 'first_name']
        verbose_name = 'Background Check'
        verbose_name_plural = 'Background Checks'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.team.name if self.team else 'No Team'}"

    def is_valid(self):
        """Check if background check clearance date is valid (not expired)"""
        from datetime import date
        return self.clearance_date > date.today()


class Roster(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='rosters')
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='rosters')
    inning_1 = models.JSONField(default=dict, blank=True, null=True, help_text='Field positions for inning 1')
    inning_2 = models.JSONField(default=dict, blank=True, null=True, help_text='Field positions for inning 2')
    inning_3 = models.JSONField(default=dict, blank=True, null=True, help_text='Field positions for inning 3')
    inning_4 = models.JSONField(default=dict, blank=True, null=True, help_text='Field positions for inning 4')
    inning_5 = models.JSONField(default=dict, blank=True, null=True, help_text='Field positions for inning 5')
    inning_6 = models.JSONField(default=dict, blank=True, null=True, help_text='Field positions for inning 6')
    lineup = models.JSONField(default=list, blank=True, null=True, help_text='Batting lineup order')
    validation_status = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rosters'
        unique_together = ('event', 'team')
        ordering = ['-created_at']
        verbose_name = 'Roster'
        verbose_name_plural = 'Rosters'

    def __str__(self):
        return f"Roster for {self.team.name} - {self.event.name}"


class EmailSettings(models.Model):
    """Singleton model to store email/SMTP configuration and sandbox settings"""
    # SMTP Configuration
    smtp_host = models.CharField(max_length=255, default='smtp.gmail.com')
    smtp_port = models.IntegerField(default=587)
    smtp_username = models.CharField(max_length=255, blank=True, null=True)
    smtp_password = models.CharField(max_length=255, blank=True, null=True, help_text='Stored in plain text')
    smtp_use_tls = models.BooleanField(default=True)
    from_email = models.EmailField(blank=True, null=True)
    reply_to_email = models.EmailField(blank=True, null=True)

    # Sandbox Mode
    sandbox_mode = models.BooleanField(default=False, help_text='When enabled, all emails are sent to the sandbox email address')
    sandbox_email = models.EmailField(blank=True, null=True, help_text='Email address to receive all emails when sandbox mode is enabled')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'email_settings'
        verbose_name = 'Email Settings'
        verbose_name_plural = 'Email Settings'

    def __str__(self):
        return f"Email Settings (Sandbox: {'ON' if self.sandbox_mode else 'OFF'})"

    @classmethod
    def get_settings(cls):
        """Get or create the singleton email settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

    def get_recipient(self, original_email):
        """Return the appropriate recipient email based on sandbox mode"""
        if self.sandbox_mode and self.sandbox_email:
            return self.sandbox_email
        return original_email
