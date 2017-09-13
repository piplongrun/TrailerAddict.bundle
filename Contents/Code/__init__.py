VERSION = '2.2'
API_URL = 'https://api.tadata.me/imdb2ta/v2/?imdb_id=%s' # %s = imdb id

POST_URL = 'https://www.traileraddict.com/ajax/film_popular.php'
POST_BODY = 'page=%d&filmid=%s' # %d = page, %s = Trailer Addict movie id

TYPE_ORDER = ['trailer', 'feature_trailer', 'theatrical_trailer', 'behind_the_scenes', 'interview', 'deleted_scene']
TYPE_MAP = {
	'trailer': TrailerObject,
	'feature_trailer': TrailerObject,
	'theatrical_trailer': TrailerObject,
	'behind_the_scenes': BehindTheScenesObject,
	'interview': InterviewObject,
	'deleted_scene': DeletedSceneObject
}

####################################################################################################
def Start():

	HTTP.CacheTime = CACHE_1WEEK
	HTTP.Headers['User-Agent'] = 'Trailer Addict/%s (%s %s; Plex Media Server %s)' % (VERSION, Platform.OS, Platform.OSVersion, Platform.ServerVersion)

	if not 'movies' in Dict:
		Dict['movies'] = {}
		Dict.Save()

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

		# If we already have the required Trailer Addict movie id
		if imdb_id in Dict['movies']:

			Log("*** We've already got a Trailer Addict id: %s ***" % (Dict['movies'][imdb_id]['ta_movie_id']))

			results.Append(MetadataSearchResult(
				id = imdb_id,
				score = 100
			))

		# If not, lookup the Trailer Addict movie id
		else:

			try:
				json_obj = JSON.ObjectFromURL(API_URL % (imdb_id), sleep=2.0)
			except:
				Log("*** Failed retrieving data from %s"  % (API_URL % (imdb_id)))
				return None

			if 'error' in json_obj:
				Log('*** An error occurred: %s' % (json_obj['error']))
				return None

			ta_movie_id = json_obj['ta_id']

			if not ta_movie_id:
				return None

			html = HTML.ElementFromURL(json_obj['url'])
			poster = html.xpath('//meta[@property="og:image"]/@content')

			if len(poster) < 1:
				poster = None
			else:
				poster = 'https://%s' % (poster[0].split('//')[-1])

			# Store the Trailer Addict movie id and poster
			Dict['movies'][imdb_id] = {}
			Dict['movies'][imdb_id]['ta_movie_id'] = ta_movie_id
			Dict['movies'][imdb_id]['poster'] = poster
			Dict.Save()

			results.Append(MetadataSearchResult(
				id = imdb_id,
				score = 100
			))

	def update(self, metadata, media, lang):

		ta_movie_id = Dict['movies'][metadata.id]['ta_movie_id']
		extras = []

		for page in range(1,2):

			try:
				page = HTTP.Request(POST_URL, data=POST_BODY % (page, ta_movie_id), sleep=2.0).content # Only HTTP.Request supports a POST body
			except:
				break

			html = HTML.ElementFromString(page)

			if len(html.xpath('//a')) < 1:
				break

			for video in html.xpath('//a'):

				title = video.text
				url = video.get('href')

				# Trailers
				if title.lower() == 'trailer':
					extra_type = 'trailer'
				elif title.lower() == 'feature trailer':
					extra_type = 'feature_trailer'
				elif title.lower() == 'theatrical trailer':
					extra_type = 'theatrical_trailer'

				# Behind the scenes / Featurette
				elif 'behind the scenes' in title.lower() or 'featurette' in title.lower():
					extra_type = 'behind_the_scenes'

				# Interview
				elif 'interview' in title.lower():
					extra_type = 'interview'

					if title.lower().startswith('interview') or title.lower().startswith('generic interview'):
						title = title.split('nterview - ')[-1].split('nterview- ')[-1]

				# Deleted scene
				elif 'deleted scene' in title.lower():
					extra_type = 'deleted_scene'

				else:
					continue

				extras.append({
					'type': extra_type,
					'extra': TYPE_MAP[extra_type](
						url = 'ta://%s' % (url.lstrip('/')),
						title = title,
						thumb = Dict['movies'][metadata.id]['poster']
					)
				})

		extras.sort(key=lambda e: TYPE_ORDER.index(e['type']))

		for extra in extras:
			metadata.extras.add(extra['extra'])
