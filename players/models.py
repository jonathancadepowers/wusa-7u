from django.db import models


class Manager(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

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
    manager_secret = models.CharField(max_length=100)

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'players'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
