import certifi
import requests

VERSION = '3.0'
API_URL = 'https://api.tadata.me/imdb2ta/v2/?imdb_id=%s'
TAC_URL = 'https://traileraddict.cache.tadata.me/%s'

TYPE_ORDER = ['trailer', 'feature_trailer', 'theatrical_trailer', 'behind_the_scenes', 'interview', 'deleted_scene']
TYPE_MAP = {
	"trailer": TrailerObject,
	"feature_trailer": TrailerObject,
	"theatrical_trailer": TrailerObject,
	"behind_the_scenes": BehindTheScenesObject,
	"interview": InterviewObject,
	"deleted_scene": DeletedSceneObject
}

HTTP_HEADERS = {
	"User-Agent": "Trailer Addict/%s (%s %s; Plex Media Server %s)" % (VERSION, Platform.OS, Platform.OSVersion, Platform.ServerVersion)
}

####################################################################################################
def Start():

	pass

####################################################################################################
class TrailerAddictAgent(Agent.Movies):

	name = 'Trailer Addict'
	languages = [Locale.Language.NoLanguage]
	primary_provider = False
	contributes_to = [
		'com.plexapp.agents.imdb',
		'com.plexapp.agents.themoviedb'
	]

	def search(self, results, media, lang):

		if media.primary_agent == 'com.plexapp.agents.imdb':

			imdb_id = media.primary_metadata.id

		elif media.primary_agent == 'com.plexapp.agents.themoviedb':

			# Get the IMDb id from the Movie Database Agent
			imdb_id = Core.messaging.call_external_function(
				'com.plexapp.agents.themoviedb',
				'MessageKit:GetImdbId',
				kwargs = dict(
					tmdb_id = media.primary_metadata.id
				)
			)

			if not imdb_id:
				Log("*** Could not find IMDb id for movie with The Movie Database id: %s ***" % (media.primary_metadata.id))
				return None

		results.Append(MetadataSearchResult(
			id = imdb_id,
			score = 100
		))

	def update(self, metadata, media, lang):

		r = requests.get(API_URL % (metadata.id), headers=HTTP_HEADERS, verify=certifi.where())

		if 'error' in r.json():
			Log("*** An error occurred: %s ***" % (r.json()['error']))
			return None

		poster = r.json()['image'] if 'image' in r.json() else None
		extras = []

		r = requests.get(TAC_URL % (r.json()['url'].split('/')[-1]), headers=HTTP_HEADERS, verify=certifi.where())
		html = HTML.ElementFromString(r.text)

		for video in html.xpath('//a[@class="m_title"]'):

			title = video.text.strip()

			if 'tv spot' in title.lower():
				continue

			url = video.get('href')

			# Trailers
			if title.lower() in ['trailer', 'international trailer', 'trailer a', 'trailer b'] and Prefs['add_trailers']:
				extra_type = 'trailer'
			elif title.lower() == 'feature trailer' and Prefs['add_feature_trailers']:
				extra_type = 'feature_trailer'
			elif title.lower() == 'theatrical trailer' and Prefs['add_theatrical_trailers']:
				extra_type = 'theatrical_trailer'

			# Behind the scenes / Featurette
			elif ('behind the scenes' in title.lower() or 'featurette' in title.lower()) and Prefs['add_featurettes']:
				extra_type = 'behind_the_scenes'

			# Interview
			elif 'interview' in title.lower() and Prefs['add_interviews']:
				extra_type = 'interview'

				if title.lower().startswith('interview') or title.lower().startswith('generic interview'):
					title = title.split('nterview - ')[-1].split('nterview- ')[-1]

			# Deleted scene
			elif 'deleted scene' in title.lower() and Prefs['add_deleted_scenes']:
				extra_type = 'deleted_scene'

			else:
				continue

			extras.append({
				'type': extra_type,
				'extra': TYPE_MAP[extra_type](
					url = 'ta://%s' % (url.lstrip('/')),
					title = title,
					thumb = poster
				)
			})

		extras.sort(key=lambda e: TYPE_ORDER.index(e['type']))

		for extra in extras:
			metadata.extras.add(extra['extra'])
