from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import datetime
from . import validators

# Create your models here.
class Reputation (models.Model):
    points = models.IntegerField(default = 0)
    lastUpTime = models.DateTimeField(auto_now=True)
    lastUpUser = models.ForeignKey('User', on_delete=models.CASCADE, null=True, blank=True, related_name="lastupuser")

class User(AbstractUser):
    class Role(models.TextChoices):
        GUEST = 'G', _('Guest')
        CREATOR = 'C', _('Creator')
        ADMIN = 'A', _('Admin')

    role = models.CharField(
        max_length=2,
        choices=Role.choices,
        default=Role.GUEST,
    )
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=50, default='')
    surname = models.CharField(max_length=50, default='')
    image = models.ImageField(upload_to='profiles/', default='/profiles/default_img.jpg', blank=False, null=False)
    registered = models.DateTimeField(auto_now=True)
    reputation = models.ForeignKey(Reputation, on_delete=models.CASCADE, null=True, blank=True )
    is_active = models.BooleanField(default = True)

class GroupPhase(models.Model):
    num_of_groups = models.IntegerField()

class Team(models.Model):
    name = models.CharField(max_length=30, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='teams/', default='teams/team.png', blank=False, null=False)
    def __str__(self):
        return self.name

class Tournament(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=200)
    class Type(models.TextChoices):
        GROUP_ELIMINATION = 'G&E', _('Group&Elimination')
        ELIMINATION = 'ELIMINATION', _('Elimination')
    type = models.CharField(
        max_length=11,
        choices=Type.choices,
        default=Type.GROUP_ELIMINATION,
    )
    num_of_teams = models.IntegerField(null=True, blank=True)
    num_of_groups = models.IntegerField(null=True, blank=True)
    teams_promoted = models.IntegerField(null=True, blank=True, default=2)
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('ACTIVE')
        FINISHED = 'FINISHED', _('FINISHED')
        APPLICATIONS_IN_PROGRESS = 'AIP', _('AIP')
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.APPLICATIONS_IN_PROGRESS
    )
    group_phase = models.ForeignKey(GroupPhase, on_delete=models.CASCADE, null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    num_of_apps = models.IntegerField(null=True, blank=True, default=0)
    applications_open_until = models.DateField(null=True, blank=True, validators=[validators.validate_date])
    isGenerated = models.BooleanField(default = False)
    start_date = models.DateField(null=True, blank=True, validators=[validators.validate_date])
    winner = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name="winner")
    runner = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name="runner")
    bronzer = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name="bronzer")

class EliminationPhase(models.Model):
    num_of_rounds = models.IntegerField()
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True, blank=True)

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True )
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True, blank=True)
    text = models.CharField(max_length=100)
    time = models.DateTimeField(auto_now=True)

class Group(models.Model):
    name = models.CharField(max_length=20)
    group_phase = models.ForeignKey(GroupPhase, on_delete=models.CASCADE)
    num_of_teams = models.IntegerField(default=0)
    matches_generated = models.BooleanField(default = False)


class MatchDate(models.Model):
    date = models.DateField(validators=[validators.validate_date])
    time = models.TimeField()
    def __str__(self):
        return (str(self.date) + ', ' + (str(self.time))[:-3])


class Participation(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    num_of_played_games = models.IntegerField(default=0)
    num_of_victories = models.IntegerField(default=0)
    num_of_defeats = models.IntegerField(default=0)
    num_of_draws = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    goals_against = models.IntegerField(default=0)
    goals_scored = models.IntegerField(default=0)
    goal_diff = models.IntegerField(null=True, blank=True, default=0)

class Player(models.Model):
    name = models.CharField(max_length=30, default='')
    lastname = models.CharField(max_length=30, default='')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='players/', default='players/player.png', blank=True, null=True)
    pin = models.CharField(unique=True, max_length=15, default='')
    number = models.IntegerField(range(1,99))
    def __str__(self):
        return str(self.number) + ', ' + self.name + ' ' + self.lastname



class EliminationRound(models.Model):
    num_of_games = models.IntegerField(null=True, blank=True, default=0)
    name = models.CharField(max_length=30)
    elimination_phase = models.ForeignKey(EliminationPhase, on_delete=models.CASCADE, null=True, blank=True)
    isCurrent = models.BooleanField(default = False)

class Match(models.Model):
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team1", null=True, blank=True)
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team2", null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    team1_goals = models.IntegerField(default=0)
    team2_goals = models.IntegerField(default=0)
    winner_id = models.IntegerField(null=True, blank=True)
    elimination_round = models.ForeignKey(EliminationRound, on_delete=models.CASCADE, null=True, blank=True)
    date = models.ForeignKey(MatchDate, on_delete=models.CASCADE, null=True, blank=True)
    isPlayed = models.BooleanField(default=False)
    nextMatch = models.ForeignKey('Match', null=True, blank=True, on_delete=models.CASCADE)

class Scorer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, null=True, blank=True)
    minute = models.IntegerField(default = 0)

class TeamApplication(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True, blank=True)

class Moderator(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True, blank=True)




