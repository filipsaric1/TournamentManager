from django.shortcuts import render, redirect
from .forms import UserForm, TeamForm, AuthForm, UserFormAdmin,PlayerForm, PasswordResetForm,  TournamentForm, ModeratorForm,PlayerEditForm, TeamApplicationForm, UserEditForm, MatchDateForm, MatchDatePicker, ScorerForm, CommentForm
from .models import Team, Player, Tournament, TeamApplication, User, Moderator, Reputation, EliminationPhase, EliminationRound, GroupPhase, Participation, Group, Match, Scorer, Comment
from django.contrib.auth.decorators import login_required
from .decorators import creator_required, admin_required
import random, math, itertools, sys, operator, datetime
from collections import Counter
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text, DjangoUnicodeDecodeError
from .tokens import tokenGenerator
from django.core.mail import EmailMessage
from django.conf import settings
import string
from .timeDateValidators import matchPlayable, isInFuture,getMatchDatesInFuture
from django.contrib.auth.views import LoginView


# Create your views here.
class Login(LoginView):
    template_name = 'auth/login.html'
    form_class = AuthForm
def handler404(request):
    return render(request, 'error/404.html', status=404)
def handler500(request):
    return render(request, 'error/500.html', status=500)
def handler401(request):
    return render(request, 'error/401.html', status=401)
@login_required(login_url='/login')
def changePassword(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            return render(request, 'auth/passwordChange.html', {'success': True})
        else:
            return render(request, 'auth/passwordChange.html', {'success': False})

def register(request):
    if request.method == 'GET':
        userForm = UserForm()
        return render(request, 'auth/register.html', {'form':userForm})
    elif request.method == 'POST':
        userForm = UserForm(request.POST)
        if userForm.is_valid():
            user = userForm.save(commit = False)
            repo = Reputation()
            repo.save()
            user.reputation = repo
            user.save()
            current_site = get_current_site(request)
            email_subject = 'Activate Your Account',
            message = render_to_string('auth/activate.html',
            {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.id)),
                'token': tokenGenerator.make_token(user)
            })
            email_message = EmailMessage(
                email_subject,
                message,
                settings.EMAIL_HOST_USER,
                to=[user.email]
            )
            user.delete()
            return render(request, 'auth/activationNote.html', {'type': 'sent'})
        else:
            return render(request, 'auth/register.html', {'form':userForm})
    else:
        return HttpResonseNotAllowed()
def activateAccount(request, uidb64, token):
    if request.method == "GET":
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id = uid)
        except User.DoesNotExist:
            return render(request, 'error/404.html')
        except Exception as identifier:
            return render(request, 'error/404.html')
        if tokenGenerator.check_token(user, token):
            user.is_active = True
            user.save()
            return redirect('/login')
        else:
            return render(request, 'error/404.html')
def verifyReset(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id = uid)
    except User.DoesNotExist:
        return render(request, 'error/404.html')
    except Exception as identifier:
        return render(request, 'error/404.html')
    if tokenGenerator.check_token(user, token):
        if request.method == "GET":
            form = PasswordResetForm()
            return render(request, 'auth/resetPassword.html', {'form': form})
        if request.method == "POST":
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                user.set_password(form.getPassword1())
                user.save()
                return render(request, 'auth/resetStatus.html', {'success':True})
            else:
                return render(request, 'auth/resetStatus.html', {'success':False})
    else:
        return render(request, 'error/404.html')


def forgotPassword(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email = email)
        except User.DoesNotExist:
            return render(request, 'auth/forgotPassword.html', {'post': True, 'mailDoesNotExist': True})
        current_site = get_current_site(request)
        email_subject = 'Reset Your Password',
        message = render_to_string('auth/reset.html',
        {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.id)),
            'token': tokenGenerator.make_token(user)
        })
        email_message = EmailMessage(
            email_subject,
            message,
            settings.EMAIL_HOST_USER,
            to=[user.email]
        )
        email_message.send()
        return render(request, 'auth/forgotPassword.html', {'post': False})
    else:
        return render(request, 'auth/forgotPassword.html', {'post': False})

@login_required(login_url='/login')
def index(request):
    tournaments = Tournament.objects.filter(status = Tournament.Status.ACTIVE)
    teams = Team.objects.filter(owner = request.user)
    teams_num = Team.objects.all().count()
    tournaments_num = Tournament.objects.all().count()
    matches_num = Match.objects.all().count()
    users_num = User.objects.all().count()

    return render(request, 'index.html', {'tournaments': tournaments, 'teams': teams, 'users_num': users_num, 'tournaments_num': tournaments_num, 'teams_num': teams_num, 'matches_num': matches_num})

@login_required(login_url='/login')
def createTeam(request):
    allTeams = Team.objects.all().filter(owner=request.user)
    teamForm = TeamForm()
    if request.method == 'POST':
        teamForm = TeamForm(request.POST or None, request.FILES or None)
        if teamForm.is_valid():
            team = teamForm.save(commit = False)
            team.owner = request.user
            team.save()
            return redirect('/ownTeam/' + str(team.id))
        else:
            return render(request, 'error/teamCreationError.html')
    return render(request, 'createTeam.html', {'form': teamForm, 'teams': allTeams})


@login_required(login_url='/login')
def ownTeam(request, tid):
    try:
        teams = Team.objects.filter(owner = request.user)
        allPlayers = Player.objects.all().filter(team = Team.objects.get(id=tid))
        team = Team.objects.get(id = tid)
    except Team.DoesNotExist:
        return render(request, 'error/400.html')
    if request.user != Team.objects.get(id = tid).owner and request.user.role != User.Role.ADMIN:
        return render(request, 'error/401.html')
    if request.method == "POST":
        form = TeamForm(request.POST or None, request.FILES or None, instance = team)
        if form.is_valid():
            team = form.save()
            team.save()
    matches = Match.objects.filter(team1 = team, isPlayed=True)
    matches2 = Match.objects.filter(team2 = team, isPlayed = True)
    matches = matches | matches2
    form = TeamForm(instance = team)
    winner = list(Tournament.objects.filter(winner = team))
    runner = list(Tournament.objects.filter(runner = team))
    bronzer = list(Tournament.objects.filter(bronzer = team))
    trophies = winner + bronzer + runner
    editForm = TeamForm(instance = team)
    return render(request, 'ownTeam.html', {'editForm': editForm,'trophies': trophies, 'form': form ,'players': allPlayers, 'matches': matches,'matches10': matches[:10],  'teams': teams, 'team': team})
@login_required(login_url='/login')
def addPlayer(request, tid):
    try:
        user = Team.objects.get(id = tid).owner
    except Team.DoesNotExist:
        return render(request, 'error/400.html')
    if user != request.user and request.user.role != User.Role.ADMIN:
        return render(request, 'error/401.html')
    if request.method == "POST":
        playerForm = PlayerForm(request.POST, request.FILES)
        if playerForm.is_valid():
            player = playerForm.save(commit=False)
            players = Player.objects.filter(team = Team.objects.get(id = tid))
            for _player in players:
                if _player.number == player.number:
                    return render(request, 'error/playerRegisterError.html')
            player.team = Team.objects.get(id = tid )
            if player.team.owner != request.user and request.user.role != User.Role.ADMIN:
                return render(request, 'error/401.html')
            player.save()
            return redirect("/ownTeam/" + str(tid))
        else:
            return render(request, 'error/playerRegisterError.html')
    playerForm = PlayerForm()
    playerForm.fields['team'] = Team.objects.get(id = tid)
    return render(request, 'addPlayer.html', {'form': playerForm, 'teams': Team.objects.filter(owner = request.user), 'team': Team.objects.get(id=tid)})
@login_required()
@creator_required
def addTournament(request):
    if request.method == 'POST':
        form = TournamentForm(request.POST)
        if form.is_valid():
            tournament = form.save(commit = False)
            tournament.creator = request.user
            tournament.save()
            return redirect('/tournament/' + str(tournament.id))
    tournamentForm = TournamentForm()
    return render (request, 'addTournament.html', {'form': tournamentForm, 'teams': Team.objects.filter(owner = request.user)})

@login_required(login_url='/login')
def othTeam(request, tid):
    try:
        allPlayers = Player.objects.all().filter(team = Team.objects.get(id=tid))
        team = Team.objects.get(id = tid)
    except Player.DoesNotExist:
        return render(request, 'error/404.html')
    except Team.DoesNotExist:
        return render(request, 'error/404.html')
    matches = Match.objects.filter(team1 = team, isPlayed = True)
    matches2 = Match.objects.filter(team2 = team, isPlayed = True)
    matches = matches | matches2
    winner = list(Tournament.objects.filter(winner = team))
    runner = list(Tournament.objects.filter(runner = team))
    bronzer = list(Tournament.objects.filter(bronzer = team))
    trophies = winner + bronzer + runner
    return render(request, 'othTeam.html', {'trophies': trophies, 'players': allPlayers, 'matches': matches,'matches10': matches[0:10],'team':team, 'teams': Team.objects.filter(owner = request.user)})

@login_required(login_url='/login')
def tournaments(request):
    allTournaments = Tournament.objects.all()
    return render(request, 'tournaments.html', {'teams': Team.objects.filter(owner = request.user),'activeTournaments': allTournaments.filter(status = Tournament.Status.ACTIVE), 'aipTournaments': allTournaments.filter(status = Tournament.Status.APPLICATIONS_IN_PROGRESS), 'finishedTournaments': allTournaments.filter(status = Tournament.Status.FINISHED), })
@creator_required
def myTournaments(request):
    allTournaments = Tournament.objects.all().filter(creator = request.user)
    mods = Moderator.objects.filter(user = request.user)
    moderating = []
    for mod in mods:
        moderating.append(mod.tournament)
    return render(request, 'tournaments.html', {'teams': Team.objects.filter(owner = request.user),'moderating': moderating,'activeTournaments': allTournaments.filter(status = Tournament.Status.ACTIVE), 'aipTournaments': allTournaments.filter(status = Tournament.Status.APPLICATIONS_IN_PROGRESS), 'finishedTournaments': allTournaments.filter(status = Tournament.Status.FINISHED)})
@login_required(login_url='/login')
def apply(request, tid):
    if request.method == 'POST':
        teamAppForm = TeamApplicationForm(request.POST, request=request)
        teamApp = teamAppForm.save(commit = False)
        if teamApp.team.owner != request.user:
            return redirect('/')
        if TeamApplication.objects.filter(team = teamApp.team, tournament = Tournament.objects.all().get(id=tid)):
            return render(request, 'error/teamApplicationError.html', {'tid':teamApp.team.id})
        players = Player.objects.filter(team = teamApp.team)
        if len(players) < 2 and not isInFuture(Tournament.objects.get(id=tid).applications_open_until) :
            return render(request, 'error/teamApplicationError.html', {'tid':teamApp.team.id})
        teamApp.tournament = Tournament.objects.all().get(id=tid)
        teamApp.tournament.num_of_apps+=1
        teamApp.tournament.save()
        teamApp.save()
    return redirect('/tournaments')


@login_required(login_url='/login')
def profile(request):
    if request.method == 'GET':
        userData = UserEditForm(instance = request.user)
        commentsNum = Comment.objects.filter(user = request.user).count()
        teamsNum = Team.objects.filter(owner = request.user).count()
        try:
            reputation = Reputation.objects.get(user = request.user)
        except Reputation.DoesNotExist:
            reputation = None
        passChangeForm = PasswordChangeForm(request.user)
        return render(request, 'profile.html', {'teams': Team.objects.filter(owner = request.user), 'reputation': reputation,'passChangeForm': passChangeForm,'form': userData, 'user':request.user, 'teamsNum': teamsNum, 'commentsNum': commentsNum})
    elif request.method == 'POST':
        userData = UserEditForm(request.POST or None, request.FILES or None, instance = request.user)
        if userData.is_valid():
            userData.save()
            return redirect('/profile')
@login_required(login_url='/login')
def playerProfile(request, pid):
    try:
        player = Player.objects.get(id=pid)
    except Player.DoesNotExist:
        return render(request, 'error/401.html')
    if request.method == 'GET':
        playerData = PlayerEditForm(instance = player)
        matchesNum = Match.objects.filter(team1 = player.team).count() + Match.objects.filter(team2 = player.team).count()
        goalsNum = Scorer.objects.filter(player = player).count()
        return render(request, 'playerProfile.html', {'teams': Team.objects.filter(owner = request.user), 'player': player, 'form': playerData, 'matches': matchesNum, 'goals': goalsNum })
    elif request.method == 'POST':
        playerData = PlayerEditForm(request.POST or None, request.FILES or None, instance = player)
        if playerData.is_valid():
            playerData.save()
    return redirect('/playerProfile/' + str(player.id))
@login_required(login_url='/login')
def repUp(request, rid, tid):
    try:
        reputation = Reputation.objects.get(id = rid)
    except Reputation.DoesNotExist:
        return render (request, 'error/401.html')
    now = datetime.datetime.now()
    tz_info = reputation.lastUpTime.tzinfo
    diff = datetime.datetime.now(tz_info) - reputation.lastUpTime
    diff_s =  diff.total_seconds()
    diff = divmod(diff_s, 3600)[0]
    if diff > 0 or request.user != reputation.lastUpUser:
        reputation.lastUpTime = now
        reputation.points += 1
        reputation.points
        reputation.lastUpUser = request.user
        reputation.save()
    return redirect('/tournament/' + str(tid) + "#commentsDiv")

@login_required(login_url='/login')
def user(request, uid):
    try:
        user = User.objects.get(id = uid)
    except User.DoesNotExist:
        return render(request, 'error/401.html')
    commentsNum = Comment.objects.filter(user = user).count()
    teamsNum = Team.objects.filter(owner = user).count()
    reputation = user.reputation
    form = None
    if request.user.role == User.Role.ADMIN:
        form = UserFormAdmin(instance = user)
        if request.method == "POST":
            form = UserFormAdmin(request.POST, request.FILES, instance = user)
            if form.is_valid():
                updated = form.save()
                updated.save()
                form = UserFormAdmin(instance = updated)
    return render (request, 'user.html', {'user': user, 'reputation': reputation, 'teamsNum': teamsNum, 'commentsNum': commentsNum, 'form': form})

@login_required(login_url='/login')
def deleteComment(request, cid):
    try:
        comment = Comment.objects.get(id = cid)
    except Comment.DoesNotExist:
        return render(request, 'error/404.html')
    tournament = comment.tournament
    if tournament.creator != request.user and not Moderator.objects.filter(user = request.user, tournament = tournament) and request.user.role != User.Role.ADMIN:
        return render(request, 'error/401.html')
    if request.method == "GET":
        comment.tournament = None
        comment.save()
    return redirect("/tournament/" + str(tournament.id) + "#commentsDiv")

@login_required(login_url='/login')
def deleteTeam(request, tid):
    try:
        team = Team.objects.get(id=tid)
    except Team.DoesNotExist:
        return render(request, 'error/400.html')
    if team.owner != request.user and request.user.role != User.Role.ADMIN:
        return render(request, 'error/400.html')
    team.owner = None
    team.save()
    return redirect('/')

@login_required(login_url='/login')
def deletePlayer(request, pid):
    try:
        player = Player.objects.get(id=pid)
    except Player.DoesNotExist:
        return render(request, 'error/400.html')
    tid = player.team.id
    if player.team.owner != request.user:
        return render(request, 'error/401.html')
    player.team = None
    player.pin = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    player.save()
    return redirect('/ownTeam/' + str(tid))

@login_required(login_url='/login')
@creator_required
def deleteTournament(request, tid):
    tournament = Tournament.objects.get(id=tid)
    if tournament.creator != request.user:
        return render(request, 'error/401.html')
    tournament.delete()
    return redirect('/tournaments_org')

@login_required(login_url='/login')
def generateTournament(request, tid):
    try:
        tournament = Tournament.objects.get(id = tid)
    except Tournament.DoesNotExist:
        return render(request, 'error/400.html')
    if request.user != tournament.creator and request.user.role != User.Role.ADMIN and tournament.type == Tournament.Type.ELIMINATION:
        return render(request, 'error/401.html')
    if tournament.num_of_apps < 4 and isInFuture(tournament.start_date):
        return render(request, 'error/401.html')
    if tournament.type == Tournament.Type.GROUP_ELIMINATION and (tournament.creator == request.user or request.user.role == User.Role.ADMIN):
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
        groupPhase = GroupPhase(num_of_groups = tournament.num_of_groups)
        groupPhase.save()
        tournament.group_phase = groupPhase
        tournament.save()
        apps = TeamApplication.objects.filter(tournament = tournament)
        teams = []
        for app in apps:
            teams.append(app.team)
        tournament.num_of_apps = teams.__len__()
        if teams.__len__() % tournament.num_of_groups != 0:
            unEven = True
            counter = teams.__len__() - 2
            while 1:
                if counter % tournament.num_of_groups == 0:
                    over = teams.__len__() - counter
                    tournament.num_of_apps -= over
                    break
                counter -= 1
            j = 0
            teamsOver = []
            while j < over:
                teamsOver.append(teams.pop())
                j += 1
        else:
            unEven = False
        random.shuffle(teams)
        groups = []
        i = 0
        while i < tournament.num_of_groups:
            group = Group(name = letters[i] ,num_of_teams = tournament.num_of_apps / tournament.num_of_groups, group_phase = groupPhase)
            group.save()
            groups.append(group)
            j = 0
            while j < group.num_of_teams:
                team = teams.pop()
                part = Participation(group = group, team = team, num_of_played_games = 0, num_of_victories = 0, num_of_defeats = 0, points = 0)
                part.save()
                j+=1
            i+=1
        if unEven:
            groupIndex = 0
            while teamsOver.__len__() != 0:
                part = Participation(group = groups[groupIndex], team = teamsOver.pop(), num_of_played_games = 0, num_of_victories = 0, num_of_defeats = 0, points = 0)
                groupIndex += 1
                if groupIndex == groups.__len__():
                    groupIndex = 0
                part.save()
        tournament.status = Tournament.Status.ACTIVE
        tournament.isGenerated = True
        tournament.save()
    return redirect('/tournament/' + str(tid))

@login_required(login_url='/login')
def groupMatchMaking(request, gid):
    try:
        group = Group.objects.get(id = gid)
    except Group.DoesNotExist:
        return render(request, 'error/400.html')
    tournament = Tournament.objects.get(group_phase = group.group_phase)
    if tournament.creator != request.user and request.user.role != User.Role.ADMIN:
        return render(request, 'error/401.html')
    tournament = Tournament.objects.get(group_phase = group.group_phase)
    if tournament.creator == request.user or request.user.role == User.Role.ADMIN:
        participations = Participation.objects.filter(group = group)
        teams = []
        for part in participations:
            teams.append(part.team)
        i = 0
        j = 0
        while i < teams.__len__():
            j = i + 1
            while j < teams.__len__():
                match = Match(team1 = teams[i], team2 = teams[j], group = group)
                match.save()
                j+=1
            i+=1
        group.matches_generated = True
        group.save()
    return redirect ('/tournament/' + str(tournament.id))

@login_required(login_url='/login')
def tournament(request, tid):
    try:
        tournament = Tournament.objects.get(id = tid)
    except Tournament.DoesNotExist:
        return render(request, 'error/400.html')
    finalFlag = False
    semiFinal = None
    bronzePlayed = False
    matchesPlayedFlag = False
    firstRoundFlag = False
    roundMatches = {}
    matches = []
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.tournament = Tournament.objects.get(id = tid)
            comment.user = request.user
            comment.save()
            return redirect('/tournament/' + str(tid) + "#commentsDiv")
    flag = 'false'
    appForm = None
    if request.user.role == User.Role.GUEST or request.user != tournament.creator:
        apps = TeamApplication.objects.all()
        appList = []
        data = {}
        appForm = TeamApplicationForm(request=request)
        for app in apps:
            if app.team.owner == request.user and app.tournament == tournament:
                flag = str(app.team)
        userCanApply = isInFuture(tournament.applications_open_until)

    apps = TeamApplication.objects.filter(tournament = tournament)
    tournament.num_of_apps = len(apps)
    tournament.save()

    data = {}
    matchlist = []
    groupStageFinished = True
    scorerlist = []
    scorers = Scorer.objects.all()
    if tournament.type == Tournament.Type.GROUP_ELIMINATION:
        groupPhase = tournament.group_phase
        groups = Group.objects.filter(group_phase = groupPhase)
        for group in groups:
            if not group.matches_generated:
                groupStageFinished = False
            teams = Participation.objects.filter(group = group).order_by('-points', '-goal_diff')
            matches = Match.objects.filter(group = group)
            matchlist.append(matches)
            data[group] = teams
        for matches in matchlist:
            for scorer in scorers:
                if scorer.match in matches:
                    scorerlist.append(scorer.player)
    commentForm = CommentForm()
    comments = reversed(Comment.objects.filter(tournament = Tournament.objects.get(id = tid)))

    for matches in matchlist:
        for match in matches:
            if match.isPlayed != True:
                groupStageFinished = False
                break
        if groupStageFinished == False:
            break
    matchlist2 = []
    elimGenerated = True if EliminationPhase.objects.filter(tournament = tournament).count() != 0 else False
    if  tournament.status == Tournament.Status.FINISHED or tournament.type == Tournament.Type.ELIMINATION and tournament.status == Tournament.Status.ACTIVE or elimGenerated and tournament.status == Tournament.Status.ACTIVE:
        elim_phase = EliminationPhase.objects.get(tournament = tournament)
        rounds = EliminationRound.objects.filter(elimination_phase = elim_phase)
        for round in rounds:
            matchlist2.append(Match.objects.filter(elimination_round = round))
        elim_phase = EliminationPhase.objects.get(tournament = tournament)
        rounds = EliminationRound.objects.filter(elimination_phase = elim_phase)
        roundMatches = {}
        current_round = None
        firstRoundFlag = False
        for round in rounds:
            roundMatches[round] = Match.objects.filter(elimination_round = round)
            if round.isCurrent:
                current_round = round
        if current_round == None:
            firstRoundFlag = True
        if current_round != None:
            if current_round.num_of_games == 1 and current_round != rounds[0]:
                current_round.name = "final"
                current_round.save()
                finalFlag = True
            if current_round.num_of_games != 1:
                finalFlag = False
            bronzePlayed = False
            if EliminationRound.objects.filter(name="bronze", elimination_phase = elim_phase).count() != 0:
                match = Match.objects.get(elimination_round = EliminationRound.objects.get(name="bronze", elimination_phase = elim_phase) )
                if match.isPlayed:
                    bronzePlayed = True
            if current_round != None:
                currentRoundMatches = Match.objects.filter(elimination_round = current_round)
                matchesPlayedFlag = True
                for match in currentRoundMatches:
                    if not match.isPlayed:
                        matchesPlayedFlag = False
    for matches in matchlist2:
        for scorer in scorers:
            if scorer.match in matches:
                scorerlist.append(scorer.player)
    scorerDict = dict(Counter(scorerlist))
    scorerDictSorted = dict(sorted(scorerDict.items(),reverse = True, key=operator.itemgetter(1)))
    form = MatchDateForm()
    datePickerForm = MatchDatePicker()
    datePickerForm.fields['date'].queryset = getMatchDatesInFuture()
    winner = None
    bronzer = None
    runner = None
    if tournament.status == Tournament.Status.FINISHED:
        elim_phase = EliminationPhase.objects.get(tournament = tournament)
        finalRound = EliminationRound.objects.get(elimination_phase = elim_phase, name="final")
        bronzeRound = EliminationRound.objects.get(elimination_phase = elim_phase, num_of_games = 0)
        winnerMatch = Match.objects.get(elimination_round = finalRound)
        bronzeMatch = Match.objects.get(elimination_round = bronzeRound)
        winner = winnerMatch.team1 if winnerMatch.team1_goals > winnerMatch.team2_goals else winnerMatch.team2
        runner = winnerMatch.team1 if winnerMatch.team1_goals < winnerMatch.team2_goals else winnerMatch.team2
        bronzer = bronzeMatch.team1 if bronzeMatch.team1_goals > bronzeMatch.team2_goals else bronzeMatch.team2
    if tournament.type == Tournament.Type.GROUP_ELIMINATION and elimGenerated:
        matchlist2 = []
        scorerlist = []
        for group in groups:
            matchlist2.append(list(Match.objects.filter(group = group)))
        for round in rounds:
            matchlist2.append(list(Match.objects.filter(elimination_round = round)))
        for matches in matchlist2:
            for scorer in scorers:
                if scorer.match in matches:
                    scorerlist.append(scorer.player)
        scorerDict = dict(Counter(scorerlist))
        scorerDictSorted = dict(sorted(scorerDict.items(),reverse = True, key=operator.itemgetter(1)))
    if request.user.role == User.Role.CREATOR and request.user == tournament.creator or Moderator.objects.filter(user = request.user, tournament = tournament) or request.user.role == User.Role.ADMIN:
        modPickForm = ModeratorForm()
        creators = User.objects.filter(role = User.Role.CREATOR)
        creatorsFiltered = []
        currentTournamentMods = list(Moderator.objects.filter(tournament = tournament))
        userObjects = [mod.user for mod in currentTournamentMods]
        for creator in list(creators):
            if creator != request.user and creator not in userObjects:
                creatorsFiltered.append(creator.id)
        modPickForm.fields['user'].queryset = User.objects.filter(pk__in = creatorsFiltered)
        userCanFinish = True if request.user == tournament.creator or request.user.role == User.Role.ADMIN else False
        tournamentGenerable = not isInFuture(tournament.start_date)
        return render(request, 'tournament_org.html', {'tournamentGenerable': tournamentGenerable,'userCanFinish': userCanFinish,'mods': userObjects,'moderatorPicker': modPickForm,'elimGenerated': elimGenerated,'winner': winner, 'runner': runner, 'bronzer': bronzer,'bronzePlayed': bronzePlayed,'groupStageFinished':groupStageFinished,'matchesPlayedFlag': matchesPlayedFlag, 'finalFlag': finalFlag, 'firstRoundFlag': firstRoundFlag, 'roundMatches': roundMatches, 'data': data,'scorerDict': dict(itertools.islice(scorerDictSorted.items(), 10)), 'matchlist': matchlist, 'form': form, 'tournament': tournament, 'datePickerForm': datePickerForm, 'commentForm': commentForm, 'comments': comments, 'teams': Team.objects.filter(owner = request.user)}  )
    else:
        return render(request, 'tournament_g.html', {'userCanApply': userCanApply, 'flag': flag,'elimGenerated': elimGenerated,'winner': winner, 'runner': runner, 'bronzer': bronzer,'bronzePlayed': bronzePlayed,'groupStageFinished':groupStageFinished,'matchesPlayedFlag': matchesPlayedFlag, 'finalFlag': finalFlag, 'firstRoundFlag': firstRoundFlag, 'roundMatches': roundMatches, 'data': data,'scorerDict': dict(itertools.islice(scorerDictSorted.items(), 10)), 'matchlist': matchlist, 'appForm': appForm, 'tournament': tournament, 'datePickerForm': datePickerForm, 'commentForm': commentForm, 'comments': comments, 'teams': Team.objects.filter(owner = request.user)}  )

@login_required(login_url='/login')
@creator_required
def setMod(request, tid):
    try:
        tournament = Tournament.objects.get(id = tid)
    except Tournament.DoesNotExist:
        return render(request, 'error/404.html')
    if tournament.creator != request.user or request.method == "GET":
        return render(request, 'error/404.html')
    form = ModeratorForm(request.POST)
    if form.is_valid():
        mod = form.save(commit = False)
        if mod.user.role != User.Role.CREATOR:
            return render(request, 'error/404.html')
        mod.tournament = tournament
        mod.save()
    return redirect('/tournament/' + str(tid))

@login_required(login_url='/login')
def newMatchDate(request, tid):
    if request.user.role != User.Role.CREATOR and request.user.role != User.Role.ADMIN:
        return render(request, 'error/401.html')
    if request.method == 'POST':
        form = MatchDateForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect('/tournament/' + str(tid))

@login_required(login_url='/login')
def setMatchDate(request, mid):
    try:
        match = Match.objects.get(id = mid)
    except Match.DoesNotExist:
        return render(request, 'error/400.html')
    if match.group_id != None:
        tournament = Tournament.objects.get(group_phase = match.group.group_phase)
    else:
        tournament = match.elimination_round.elimination_phase.tournament
    if (tournament.creator != request.user and not Moderator.objects.filter(user = request.user, tournament = tournament)) and request.user.role != User.Role.ADMIN:
        return render(request, 'error/401.html')
    if request.method == 'POST':
        form = MatchDatePicker(request.POST)
        if form.is_valid():
            modelInstance = form.save(commit=False)
            match.date = modelInstance.date
            match.save()

    return redirect ('/tournament/' + str(tournament.id) + "#" + str(match.id))

@login_required(login_url='/login')
def match (request, mid):
    try:
        match = Match.objects.get(id = mid)
        if match.elimination_round:
            tournament = match.elimination_round.elimination_phase.tournament
        else:
            groupPhase = match.group.group_phase
            tournament = Tournament.objects.get(group_phase = groupPhase)
    except Match.DoesNotExist:
        return render(request, 'error/400.html')
    team1Form = ScorerForm(initial={'match': match})
    team1Form.fields['player'].queryset = Player.objects.filter(team = match.team1)
    team2Form = ScorerForm(initial={'match': match})
    team2Form.fields['player'].queryset = Player.objects.filter(team = match.team2)
    allScorers = Scorer.objects.filter(match = match)
    team1Scorers = []
    team2Scorers = []
    for scorer in allScorers:
        if scorer.player.team == match.team1:
            team1Scorers.append(scorer)
        else:
            team2Scorers.append(scorer)
    elimFlag = False
    if match.elimination_round_id != None:
        elimFlag = True
    if request.user.role == User.Role.CREATOR and request.user == tournament.creator or Moderator.objects.filter(user = request.user, tournament = tournament) or request.user.role == User.Role.ADMIN:
        playable = matchPlayable(match) if match.date_id != None else False
        finishable = True if not match.isPlayed and (match.team1_goals != match.team2_goals) else False
        return render(request, 'match.html', {'playable':playable, 'elimFlag': elimFlag,'match': match, 'team1Form': team1Form, 'team2Form': team2Form, 'team1Scorers': team1Scorers, 'team2Scorers': team2Scorers, 'finishable': finishable})
    else:
        return render(request, 'match_g.html', {'match': match, 'teams':Team.objects.filter(owner = request.user), 'team1Scorers': team1Scorers, 'team2Scorers': team2Scorers, })


@login_required(login_url='/login')
def addScorer(request, mid):
    if request.method == 'POST':
        data = ScorerForm(request.POST)
        try:
            match = Match.objects.get(id = mid)
        except Match.DoesNotExist:
            return render(request, 'error/400.html')
        if match.elimination_round:
            tournament = match.elimination_round.elimination_phase.tournament
            if tournament.creator != request.user and not Moderator.objects.filter(user = request.user, tournament = tournament) and request.user.role != User.Role.ADMIN:
                return render(request, 'error/401.html')
        else:
            match = Match.objects.get(id = mid)
            group = match.group
            group_phase = group.group_phase
            tournament = Tournament.objects.get(group_phase = group_phase)
            if tournament.creator != request.user and not Moderator.objects.filter(user = request.user, tournament = tournament):
                return render(request, 'error/401.html')
        if data.is_valid():
            scorer = data.save(commit=False)
            scorer.match = match
            scorer.save()
            if (match.team1 == scorer.player.team):
                match.team1_goals +=1
                match.save()
            else:
                match.team2_goals +=1
                match.save()
    return redirect('/match/' + str(match.id))

@login_required(login_url='/login')
def finishMatch(request, mid):
    try:
        match = Match.objects.get(id = mid)
    except Match.DoesNotExist:
        return render(request, 'error/400.html')
    if not matchPlayable(match):
        render(request, 'error/400.html')
    if match.elimination_round:
        tournament = match.elimination_round.elimination_phase.tournament
        if tournament.creator != request.user and not Moderator.objects.filter(user = request.user, tournament = tournament) and request.user.role != User.Role.ADMIN:
            return render(request, 'error/401.html')
        match = Match.objects.get(id = mid)
        draw = False
        match.isPlayed = True
        if match.team1_goals == match.team2_goals:
            return redirect('/match/' + str(mid))
        if match.team1_goals > match.team2_goals:
            match.winner_id = match.team1_id
        else:
            match.winner_id = match.team2_id
        match.save()

    else:
        match = Match.objects.get(id = mid)
        group = match.group
        group_phase = group.group_phase
        tournament = Tournament.objects.get(group_phase = group_phase)
        if tournament.creator != request.user and not Moderator.objects.filter(user = request.user, tournament = tournament) and request.user.role != User.Role.ADMIN:
            return render(request, 'error/401.html')
        draw = False
        match.isPlayed = True
        if match.team1_goals > match.team2_goals:
            match.winner = match.team1
        elif match.team1_goals < match.team2_goals:
            match.winner = match.team2
        else:
            draw = True
        match.save()
        if not draw:
            part1 = Participation.objects.get(team = match.winner, group = match.group)
            part1.points+=3
            part1.goals_scored += match.team1_goals if match.winner == match.team1 else match.team2_goals
            part1.goals_against += match.team2_goals if match.winner == match.team1 else match.team1_goals
            part1.goal_diff = part1.goals_scored - part1.goals_against
            part1.num_of_played_games+=1
            part1.num_of_victories+=1
            part1.save()
            part2 = Participation.objects.get(team = match.team1 if match.winner == match.team2 else match.team2, group=match.group)
            part2.goals_against+= match.team1_goals if match.winner == match.team1 else match.team2_goals
            part2.goals_scored+=match.team2_goals if match.winner == match.team1 else match.team1_goals
            part2.goal_diff = part2.goals_scored - part2.goals_against
            part2.num_of_played_games+=1
            part2.num_of_defeats+=1
            part2.save()
        elif draw:
            part1 = Participation.objects.get(team = match.team1, group = match.group)
            part1.points+=1
            part1.goals_against+=match.team1_goals
            part1.goals_scored+=match.team2_goals
            part1.goal_diff = part1.goals_scored - part1.goals_against
            part1.num_of_draws+=1
            part1.num_of_played_games+=1
            part1.save()
            part2 = Participation.objects.get(team = match.team2, group = match.group)
            part2.points+=1
            part2.goals_against+=match.team1_goals
            part2.goals_scored+=match.team2_goals
            part2.goal_diff = part2.goals_scored - part2.goals_against
            part2.num_of_draws+=1
            part2.num_of_played_games+=1
            part2.save()
    return redirect('/tournament/' + str(tournament.id) + "#" + str(mid))




def handler404(request, *args, **argv):
    response = render_to_response('error/404.html', {}, context_instance=RequestContext(request))
    response.status_code = 404
    return response

@login_required(login_url='/login')
def teamApplicationError(request):
    return render(request, 'error/teamApplicationError.html')
def deleteScorer(request, sid):
    try:
        scorer = Scorer.objects.get(id = sid)
    except Scorer.DoesNotExist:
        return render(request, 'error/400.html')
    match = scorer.match
    if (match.team1 == scorer.player.team):
        match.team1_goals -=1
        match.save()
    else:
        match.team2_goals -=1
        match.save()
    scorer.delete()
    return redirect('/match/' + str(match.id))

@login_required(login_url='/login')
def generateElimination(request, tid):
    try:
        tournament = Tournament.objects.get(id = tid)
    except Tournament.DoesNotExist:
        return render(request, 'error/400.html')
    if tournament.creator != request.user and request.user.role != User.Role.ADMIN:
        return redirect('/')
    if tournament.type == Tournament.Type.ELIMINATION:
        if tournament.num_of_apps < 4 and isInFuture(tournament.start_date):
            return render(request, 'error/400.html')
        teamApps = list(TeamApplication.objects.filter(tournament = tournament))
        teams=[]
        for app in teamApps:
            teams.append(app.team)
    if tournament.type == Tournament.Type.GROUP_ELIMINATION:
        groupPhase = tournament.group_phase
        groups = Group.objects.filter(group_phase = groupPhase)
        matchlist = []
        teams = []
        if tournament.type == Tournament.Type.GROUP_ELIMINATION and tournament.status == Tournament.Status.ACTIVE:
            for group in groups:
                parts = list(Participation.objects.filter(group = group).order_by('-points', '-goal_diff', '-goals_scored'))
                team1 = parts[0].team
                team2 = parts[1].team
                teams.append(team1)
                teams.append(team2)
                matches = Match.objects.filter(group = group)
                matchlist.append(matches)
            groupStageFinished = True
            for matches in matchlist:
                for match in matches:
                    if not match.isPlayed:
                        return redirect('/')
            cnti = 0
            cntj = teams.__len__() - 1
            teamsDrawList = []
            while cnti < cntj:
                teamsDrawList.append(teams[cnti])
                teamsDrawList.append(teams[cntj])
                cnti+=1
                cntj-=1
            teams = teamsDrawList

    teamsCount = teams.__len__()
    if not math.log(teamsCount, 2).is_integer():
        i = teamsCount + 1
        while True:
            if math.log(i, 2).is_integer():
                toNextRoundCount = i - teamsCount
                break
            i+=1
        toNextRoundTeams = []
        z = 0
        while z < toNextRoundCount:
            toNextRoundTeams.append(teams.pop())
            z+=1
        firstRoundMatches = (teamsCount - toNextRoundCount) / 2
        roundsNum = math.log(i, 2)
        eliminationPhase = EliminationPhase(num_of_rounds = roundsNum, tournament = tournament)
        eliminationPhase.save()
        j = 0
        otherRoundsMatchCount = i/4
        while j < roundsNum:
            if j == 0:
                round = EliminationRound(num_of_games = firstRoundMatches, name="1 / "  + str(firstRoundMatches), elimination_phase = eliminationPhase)
                round.save()
            else:
                round = EliminationRound(num_of_games = otherRoundsMatchCount, name="1 / "  + str(otherRoundsMatchCount), elimination_phase = eliminationPhase)
                round.save()
                otherRoundsMatchCount /= 2
            j+=1
        rounds = list(EliminationRound.objects.filter(elimination_phase = eliminationPhase))
        nextRoundMatches = []
        for round in rounds[::-1]:
            roundIndex = rounds.__len__() - 1
            j=0
            if round.num_of_games == 1 and round != rounds[0]: #final
                match = Match(elimination_round = round)
                match.save()
                nextRoundMatches.append(match)
            elif round.num_of_games == i/4 and round != rounds[0]:
                nextMatchIndex = 0
                tmp = nextRoundMatches
                nextRoundMatches = []
                j=0
                while j < round.num_of_games:
                    match = Match(elimination_round = round, nextMatch = tmp[nextMatchIndex])
                    if match.team1_id == None and toNextRoundTeams:
                        match.team1 = toNextRoundTeams.pop()
                    if match.team2_id == None and toNextRoundTeams:
                        match.team2 = toNextRoundTeams.pop()
                    match.save()
                    nextRoundMatches.append(match)
                    if j % 2 == 1 and j != 0:
                        nextMatchIndex+=1
                    j+=1

            elif round.num_of_games == firstRoundMatches and round == rounds[0]:
                j=0
                nextMatchIndex = 0
                tmp = nextRoundMatches
                nextRoundMatches = []
                nextMatchesCount = {}
                for match in tmp:
                    nextMatchesCount[match] = 0
                    if match.team1_id != None:
                        nextMatchesCount[match] += 1
                    if match.team2_id != None:
                        nextMatchesCount[match] += 1

                while j < round.num_of_games:
                    for match in tmp:
                        if match.team1_id == None and nextMatchesCount[match] < 2:
                            newmatch = Match(elimination_round = round, nextMatch = match)
                            newmatch.save()
                            nextMatchesCount[match] += 1
                            break
                        if match.team2_id == None and nextMatchesCount[match] < 2:
                            newmatch = Match(elimination_round = round, nextMatch = match)
                            newmatch.save()
                            nextMatchesCount[match] += 1
                            break
                    j+=1
            else:
                nextMatchIndex = 0
                tmp = nextRoundMatches
                nextRoundMatches = []
                j=0
                while j < round.num_of_games:
                    match = Match(elimination_round = round, nextMatch = tmp[nextMatchIndex])
                    match.save()
                    nextRoundMatches.append(match)
                    if j % 2 == 1 and j != 0:
                        nextMatchIndex+=1
                    j+=1
            roundIndex-=1
        tournament.isGenerated = True
        tournament.status = Tournament.Status.ACTIVE
        tournament.save()
        return redirect('/tournament/' + str(tid)  +  "#" + str(rounds[0].id))

    roundsNum = math.log(teams.__len__(), 2)
    eliminationPhase = EliminationPhase(num_of_rounds = roundsNum, tournament = tournament)
    eliminationPhase.save()
    i = 0
    matchesInRound = teamsCount / 2
    while i < roundsNum:
        round = EliminationRound(num_of_games = matchesInRound, name="1 / "  + str(matchesInRound), elimination_phase = eliminationPhase)
        round.save()
        i+=1
        matchesInRound /= 2
    rounds = list(EliminationRound.objects.filter(elimination_phase = eliminationPhase))
    nextRoundMatches = []
    for round in rounds[::-1]:
        i=0
        if round.num_of_games == 1: #final
            match = Match(elimination_round = round)
            match.save()
            nextRoundMatches.append(match)
        else:
            nextMatchIndex = 0
            tmp = nextRoundMatches
            nextRoundMatches = []
            while i < round.num_of_games:
                match = Match(elimination_round = round, nextMatch = tmp[nextMatchIndex])
                match.save()
                nextRoundMatches.append(match)
                if i % 2 == 1 and i != 0:
                    nextMatchIndex+=1
                i+=1
    tournament.isGenerated = True
    tournament.status = Tournament.Status.ACTIVE
    tournament.save()
    return redirect('/tournament/' + str(tid))

@login_required(login_url='/login')
def generateNextRound(request, tid):
    try:
        tournament = Tournament.objects.get(id = tid)
    except Tournament.DoesNotExist:
        return render(request, 'error/400.html')
    if tournament.creator != request.user and request.user.role != User.Role.ADMIN and not Moderator.objects.get(tournament = tournament, user = request.user) or tournament.status == Tournament.Status.APPLICATIONS_IN_PROGRESS or tournament.status == Tournament.Status.FINISHED :
        return render(request, 'error/401.html')
    eliminationPhase = EliminationPhase.objects.get(tournament = tournament)
    rounds = EliminationRound.objects.filter(elimination_phase = eliminationPhase)
    flag = False
    current = None
    i = 0
    for round in rounds:
        if round.isCurrent:
            flag = True
            current = rounds[i+1]
            round.isCurrent = False
            round.save()
            current.isCurrent = True
            current.save()
            matches = Match.objects.filter(elimination_round = rounds[i])
            winners = {}
            for match in matches:
                winners[Team.objects.get(id = match.winner_id)] = match.nextMatch
            teamApps = TeamApplication.objects.filter(tournament = tournament)
            teams = []
            for app in teamApps:
                teams.append(app.team)
            j = 0
            if current.num_of_games == 1:
                list(winners.values())[0].team1 = list(winners.keys())[0]
                list(winners.values())[0].team2 = list(winners.keys())[1]
                list(winners.values())[0].save()
                firstSemiFinalist = matches[0].team1 if matches[0].team1_goals < matches[0].team2_goals else matches[0].team2
                secondSemiFinalist = matches[1].team1 if matches[1].team1_goals < matches[1].team2_goals else matches[1].team2
                semiRound = EliminationRound(elimination_phase = eliminationPhase, name="bronze")
                semiRound.save()
                semiFinal = Match(team1 = firstSemiFinalist, team2 = secondSemiFinalist, elimination_round = semiRound )
                semiFinal.save()
            else:
                addedToFirst = False
                for team, match in winners.items():
                    updatedMatch = Match.objects.get(id = match.id)
                    if updatedMatch.team1_id == None:
                        updatedMatch.team1 = team
                        updatedMatch.save()
                    else:
                        updatedMatch.team2 = team
                        updatedMatch.save()
            return redirect('/tournament/' + str(tid) +  "#" + str(current.id))
        i+=1
    if not flag:
        current = rounds[0]
        current.isCurrent = True
        current.save()
        teamApps = TeamApplication.objects.filter(tournament = tournament)
        teams = []
        if tournament.type == "ELIMINATION":
            for app in teamApps:
                teams.append(app.team)
        if tournament.type == Tournament.Type.GROUP_ELIMINATION and tournament.status == Tournament.Status.ACTIVE:
            groupPhase = tournament.group_phase
            groups = Group.objects.filter(group_phase = groupPhase)
            teams = []
            for group in groups:
                parts = list(Participation.objects.filter(group = group).order_by('-points', '-goal_diff', '-goals_scored'))
                team1 = parts[0].team
                team2 = parts[1].team
                teams.append(team1)
                teams.append(team2)
            cnti = 0
            cntj = teams.__len__() - 1
            teamsDrawList = []
            while cnti < cntj:
                teamsDrawList.append(teams[cnti])
                teamsDrawList.append(teams[cntj])
                cnti+=1
                cntj-=1
            teams = teamsDrawList
        if not math.log(teams.__len__(), 2).is_integer:
            i = teamsCount + 1
            while True:
                if math.log(i, 2).is_integer():
                    toNextRoundCount = i - teamsCount
                    break
                i+=1
            toNextRoundTeams = []
            z = 0
            while z < toNextRoundCount:
                toNextRoundTeams.append(teams.pop())
                z+=1

        matches = Match.objects.filter(elimination_round = current)
        i = 0
        for match in matches:
            match.team1 = teams[i]
            match.team2 = teams[i+1]
            match.save()
            i += 2
        return redirect('/tournament/' + str(tid) +  "#" + str(current.id))


@login_required(login_url='/login')
def finishTournament(request, tid):
    try:
        tournament = Tournament.objects.get(id = tid)
    except Tournament.DoesNotExist:
        return render(request, 'error/400.html')
    if tournament.creator != request.user and request.user.role != User.Role.ADMIN:
        return render(request, 'error/401.html')
    try:
        elimination_phase = EliminationPhase.objects.get(tournament = tournament)
        rounds = EliminationRound.objects.filter(elimination_phase = elimination_phase)
        finalRound = EliminationRound.objects.get(elimination_phase = elimination_phase, name="final")
        bronzeRound = EliminationRound.objects.get(elimination_phase = elimination_phase, num_of_games = 0)
        winnerMatch = Match.objects.get(elimination_round = finalRound)
        bronzeMatch = Match.objects.get(elimination_round = bronzeRound)
        tournament.winner = winnerMatch.team1 if winnerMatch.team1_goals > winnerMatch.team2_goals else winnerMatch.team2
        tournament.runner = winnerMatch.team1 if winnerMatch.team1_goals < winnerMatch.team2_goals else winnerMatch.team2
        tournament.bronzer = bronzeMatch.team1 if bronzeMatch.team1_goals > bronzeMatch.team2_goals else bronzeMatch.team2
    except EliminationRound.DoesNotExist:
        return render(request, 'error/404.html')
    for roun in rounds:
        matches = Match.objects.filter(elimination_round = roun)
        for match in matches:
            if not match.isPlayed:
                return redirect('/')
    tournament.status = Tournament.Status.FINISHED
    tournament.save()
    return redirect('/tournament/' + str(tid))
@login_required(login_url='/login')
@admin_required
def teams(request):
    teams = Team.objects.all() or None
    if teams != None:
        teams = [team for team in teams if team.owner]
    return render(request, 'admin/teams.html', {'teams': teams})

@login_required(login_url='/login')
@admin_required
def users(request):
    users = User.objects.all() or None
    users = [user for user in users if user.role != User.Role.ADMIN]
    return render(request, 'admin/users.html', {'users': users})