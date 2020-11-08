from datetime import datetime, timedelta
from .models import Match, MatchDate

def isInFuture(date):
	today = datetime.now().date()
	return True if date > today else False
def matchPlayable(match:Match):
	matchDateTime = datetime.combine(match.date.date, match.date.time)
	now = datetime.now()
	upperLimit = now + timedelta(hours = 2)
	return True if now > matchDateTime and now < upperLimit else False

def getMatchDatesInFuture():
	matchDates = MatchDate.objects.all()
	filtered = []
	for matchDate in matchDates:
		dt = datetime.combine(matchDate.date, matchDate.time)
		if dt > datetime.now():
			filtered.append(matchDate.id)
	return MatchDate.objects.filter(id__in=filtered)
