from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import User, Team, Player, Tournament, TeamApplication, MatchDate, Match, Scorer, Comment, Moderator
from django.forms import ModelForm, DateTimeInput, TimeInput, TimeField, HiddenInput, ImageField, FileInput
from .timeDateValidators import isInFuture, getMatchDatesInFuture
import datetime
from django.contrib.auth.forms import AuthenticationForm
class DateInput(DateTimeInput):
    input_type = 'date'

class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']
class PasswordResetForm(forms.Form):
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)

    def getPassword1(self):
        return self['new_password1'].value()
    def getPassword2(self):
        return self['new_password2'].value()
    def is_valid(self):
        if self['new_password1'].value() == self['new_password2'].value() and self['new_password2'].value().__len__() > 7:
            return True
        else:
            return False

class TeamForm(ModelForm):
    image = ImageField(label=(''),required=False, widget=FileInput)
    class Meta:
        model = Team
        fields = ['name', 'image']

class PlayerForm(ModelForm):
    class Meta:
        model = Player
        fields = ['name', 'lastname', 'pin', 'image', 'number']

class TournamentForm(ModelForm):
    class Meta:
        model = Tournament
        fields = ['name','description', 'type', 'num_of_groups', 'teams_promoted', 'applications_open_until', 'start_date']
        widgets = {
            'applications_open_until': DateInput(),
            'start_date': DateInput()
        }
class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

class TeamApplicationForm(ModelForm):
    class Meta:
        model = TeamApplication
        fields = ['team']
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(TeamApplicationForm, self).__init__(*args, **kwargs)
        self.fields["team"].queryset = Team.objects.filter(owner=self.request.user)

class UserEditForm(ModelForm):
    image = ImageField(label=(''),required=False, widget=FileInput)
    class Meta:
        model = User
        fields = ['name', 'surname', 'image']
class PlayerEditForm(ModelForm):
    image = ImageField(label=(''),required=False, widget=FileInput)
    class Meta:
        model = Player
        fields = ['name', 'lastname','pin', 'number', 'image']

class MatchDateForm(ModelForm):
    class Meta:
        model = MatchDate
        fields = '__all__'
        widgets = {
            'date':DateInput(),
            'time':TimeInput()
        }
class MatchDatePicker(ModelForm):
    class Meta:
        model = Match
        fields = ['date']
class ScorerForm(ModelForm):
    class Meta:
        model = Scorer
        fields = ['player', 'match', 'minute']

class ModeratorForm(ModelForm):
    class Meta:
        model = Moderator
        fields = ['user', 'tournament']
class UserFormAdmin(ModelForm):
    roles = (
        ('C', 'CREATOR'),
        ('G', 'GUEST'),
    )
    image = ImageField(label=(''),required=False, widget=FileInput)
    role = forms.CharField(widget=forms.Select(choices=roles))
    class Meta:
        model = User
        fields = ['name', 'surname', 'image', 'role']


class AuthForm(AuthenticationForm):
    def get_invalid_login_error(self):
        try:
            user = User.objects.get(username=self.cleaned_data.get('username'))
        except User.DoesNotExist:
            return forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name}, )
        self.error_messages['inactive'] = 'This account is inactive. Check your email for activation link.'
        if not user.is_active and user:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',)
        else:
            return forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name}, )