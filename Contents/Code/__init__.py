API_URL = 'http://api.traileraddict.com/?imdb=%s' # %s = imdb id
MOVIE_URL = 'http://www.traileraddict.com/%s' # %s = slug or relative url

POST_URL = 'http://www.traileraddict.com/ajax/film_popular.php'
POST_BODY = 'page=%d&filmid=%s' # %d = page, %s = traileraddict movie id

RE_TA_MOVIE_ID = Regex('filmpop\(\d+,(\d+)\)')

TYPE_ORDER = ['trailer', 'feature_trailer', 'theatrical_trailer', 'behind_the_scenes', 'interview', 'music_video', 'deleted_scene']
TYPE_MAP = {
	'trailer': TrailerObject,
	'feature_trailer': TrailerObject,
	'theatrical_trailer': TrailerObject,
	'behind_the_scenes': BehindTheScenesObject,
	'interview': InterviewObject,
#	'music_video': MusicVideoObject,
	'music_video': SceneOrSampleObject,
	'deleted_scene': DeletedSceneObject
}

####################################################################################################
def Start():

	HTTP.CacheTime = CACHE_1WEEK

	if not 'movies' in Dict:
		Dict['movies'] = {}
		Dict.Save()

####################################################################################################
class TrailerAddictAgent(Agent.Movies):

	name = 'Trailer Addict'
	languages = [Locale.Language.English]
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

		# If we already have the required traileraddict movie id
		if imdb_id in Dict['movies']:

			Log("*** We've already got a Trailer Addict id: %s ***" % (Dict['movies'][imdb_id]['ta_movie_id']))

			results.Append(MetadataSearchResult(
				id = imdb_id,
				score = 100
			))

		# If not, lookup the traileraddict movie id
		else:

			try:
				xml = XML.ElementFromURL(API_URL % (imdb_id.strip('t')), sleep=2.0)
			except:
				return None

			link = xml.xpath('//link/text()')

			if len(link) < 1:
				return None

			slug = link[0].split('/')[3]

			try:
				html = HTML.ElementFromURL(MOVIE_URL % (slug), sleep=2.0)
			except:
				return None

			script = html.xpath('//script[contains(., "filmpop(")]/text()')

			if len(script) < 1:
				return None

			ta_movie_id = RE_TA_MOVIE_ID.search(script[0])

			if not ta_movie_id:
				return None

			poster = html.xpath('//meta[@property="og:image"]/@content')

			if len(poster) < 1:
				poster = None
			else:
				poster = 'http://%s' % (poster[0].split('//')[-1])

			# Store the traileraddict movie id and poster
			Dict['movies'][imdb_id] = {}
			Dict['movies'][imdb_id]['ta_movie_id'] = ta_movie_id.group(1)
			Dict['movies'][imdb_id]['poster'] = poster
			Dict.Save()

			results.Append(MetadataSearchResult(
				id = imdb_id,
				score = 100
			))

	def update(self, metadata, media, lang):

		ta_movie_id = Dict['movies'][metadata.id]['ta_movie_id']
		extras = []

		for page in range(1,6):

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

				# Music video
				elif 'music video' in title.lower():
					extra_type = 'music_video'

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
