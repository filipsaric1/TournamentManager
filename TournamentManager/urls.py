from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from mainapp import views
from django.conf import settings
from django.conf.urls.static import static
from mainapp.views import Login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', Login.as_view()),
    path('logout/', LogoutView.as_view()),
    path('register/', views.register, name='register'),
    path('createTeam/', views.createTeam, name='myteams'),
    path('ownTeam/<int:tid>', views.ownTeam, name="ownTeam"),
    path('othTeam/<int:tid>', views.othTeam, name="othTeam"),
    path('tournaments/', views.tournaments, name='tournaments'),
    path('myTournaments/', views.myTournaments, name='myTournaments'),
    path('apply/<int:tid>', views.apply, name='apply'),
    path('profile/', views.profile, name='profile'),
    path('playerProfile/<int:pid>', views.playerProfile, name='playerProfile'),
    path('deleteTeam/<int:tid>', views.deleteTeam, name='deleteTeam'),
    path('deletePlayer/<int:pid>', views.deletePlayer, name='deletePlayer'),
    path('deleteTournament/<int:tid>', views.deleteTournament, name='deleteTournament'),
    path('generate/<int:tid>', views.generateTournament, name='generateTournament'),
    path('matchMake/<int:gid>', views.groupMatchMaking, name='groupMatchMaking'),
    path('tournament/<int:tid>', views.tournament, name='tournament'),
    path('newMatchDate/<int:tid>', views.newMatchDate, name='newMatchDate'),
    path('setMatchDate/<int:mid>', views.setMatchDate, name='setMatchDate'),
    path('match/<int:mid>', views.match, name='match'),
    path('addScorer/<int:mid>', views.addScorer, name='addScorer'),
    path('finishMatch/<int:mid>', views.finishMatch, name='finishMatch'),
    path('teamApplicationError/', views.teamApplicationError, name='teamApplicationError'),
    path('deleteScorer/<int:sid>', views.deleteScorer, name='deleteScorer'),
    path('generateElimination/<int:tid>', views.generateElimination, name='generateElimination'),
    path('addPlayer/<int:tid>', views.addPlayer, name='addPlayer'),
    path('addTournament/', views.addTournament, name='addTournament'),
    path('generateNextRound/<int:tid>', views.generateNextRound, name='generateNextRound'),
    path('finishTournament/<int:tid>', views.finishTournament, name='finishTournament'),
    path('401', views.handler401, name='401'),
    path('repUp/<int:rid>/<int:tid>', views.repUp, name='repUp'),
    path('user/<int:uid>', views.user, name='user'),
    path('changePassword/', views.changePassword, name="changePassword"),
    path('activateAccount/<uidb64>/<token>', views.activateAccount, name='activateAccount'),
    path('setMod/<int:tid>', views.setMod, name='setMod'),
    path('forgotPassword/', views.forgotPassword, name="forgotPassword"),
    path('verifyReset/<uidb64>/<token>', views.verifyReset, name="verifyReset"),
    path('deleteComment/<int:cid>', views.deleteComment, name="deleteComment"),
    path('admin/teams/', views.teams, name="admin/teams"),
    path('admin/users/', views.users, name="admin/users")
]
handler404 = 'mainapp.views.handler404'
handler500 = 'mainapp.views.handler500'
handler401 = 'mainapp.views.handler401'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)