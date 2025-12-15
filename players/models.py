from django.db import models


class Draft(models.Model):
    rounds = models.IntegerField()
    picks_per_round = models.IntegerField()
    order = models.TextField()
    final_round_draft_order = models.TextField(blank=True, null=True)

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'managers'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Team(models.Model):
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, blank=True, related_name='teams')
    name = models.CharField(max_length=100)
    manager_secret = models.CharField(max_length=100, unique=True)
    practice_slot = models.ForeignKey('PracticeSlot', on_delete=models.SET_NULL, null=True, blank=True, related_name='teams')

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
    attended_try_out = models.BooleanField(default=True)
    draftable = models.BooleanField(default=True)

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
        return f"Practice Slot: {self.practice_slot}"


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'starred_draft_picks'
        unique_together = ('player', 'team')
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
