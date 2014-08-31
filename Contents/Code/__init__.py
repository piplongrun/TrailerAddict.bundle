API_URL = 'http://api.traileraddict.com/?imdb=%s' # %s = imdb id
MOVIE_URL = 'http://www.traileraddict.com/%s' # %s = slug or relative url

POST_URL = 'http://www.traileraddict.com/ajax/film_popular.php'
POST_BODY = 'page=1&filmid=%s' # %s = traileraddict movie id

RE_TA_MOVIE_ID = Regex('filmpop\(\d+,(\d+)\)')

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
	contributes_to = ['com.plexapp.agents.imdb']

	def search(self, results, media, lang):

		imdb_id = media.primary_metadata.id

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

		try:
			page = HTTP.Request(POST_URL, data=POST_BODY % (ta_movie_id), sleep=2.0).content # Only HTTP.Request supports a POST body
			html = HTML.ElementFromString(page)
		except:
			return None

		for video in html.xpath('//a'):

			title = video.text
			url = video.get('href')

			if 'tv spot' in title.lower() or title.lower().startswith('spot ') or title.lower().startswith('spot-') or title.lower().endswith(' spot'):
				continue

			if 'promo' in title.lower():
				continue

			if 'japanese ' in title.lower() or 'asia trailer' in title.lower():
				continue

			if 'trailer' in title.lower():
				extra = TrailerObject(
					url = 'ta://%s' % (url.lstrip('/')),
					title = title,
					thumb = Dict['movies'][metadata.id]['poster']
				)

			elif 'interview' in title.lower():
				if title.lower().startswith('interview'):
					title = title.split('nterview - ')[-1].split('nterview- ')[-1]

				extra = InterviewObject(
					url = 'ta://%s' % (url.lstrip('/')),
					title = title,
					thumb = Dict['movies'][metadata.id]['poster']
				)

			elif 'behind the scenes' in title.lower() or 'featurette' in title.lower():
				extra = BehindTheScenesObject(
					url = 'ta://%s' % (url.lstrip('/')),
					title = title,
					thumb = Dict['movies'][metadata.id]['poster']
				)

			elif 'deleted scene' in title.lower():
				extra = DeletedSceneObject(
					url = 'ta://%s' % (url.lstrip('/')),
					title = title,
					thumb = Dict['movies'][metadata.id]['poster']
				)

			else:
				extra = SceneOrSampleObject(
					url = 'ta://%s' % (url.lstrip('/')),
					title = title,
					thumb = Dict['movies'][metadata.id]['poster']
				)

			metadata.extras.add(extra)
