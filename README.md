Trailer Addict
==============
<img src="https://img.shields.io/github/release/piplongrun/TrailerAddict.bundle.png?style=flat-square">

What is Trailer Addict?
-----------------------
Trailer Addict is a metadata agent for Plex Media Server that tries to find trailers, interviews and behind the scenes videos for your movie library.

Requirements
------------
A Plex movie library with the _Plex Movie_ agent or _The Movie Database_ agent set as primary agent.

How do I install Trailer Addict?
--------------------------------
You can install Trailer Addict:

 - From within the Unsupported App Store, or:
 - Manually: See the support article "[How do I manually install a channel?](https://support.plex.tv/hc/en-us/articles/201187656-How-do-I-manually-install-a-channel-)" over at the Plex support website.

Don't forget to activate the agent in Settings > Server > Agents after installing.

Where do I download Trailer Addict?
-----------------------------------
If you want to install the agent manually or if you are interested in the source code, you can download the latest copy of the agent from Github: [releases](https://github.com/piplongrun/TrailerAddict.bundle/releases)

Limitations and Known Issues
----------------------------
 - Due to not being able to grab certain data directly I had to build a small API that converts IMDb ids to Trailer Addict ids. This API is still a bit slow due to a number of http requests it has to do. Lots of requests are cached, so the more the agent gets used, the faster it will become.
 - The source website does not offer preview images for the videos.

Where do I report issues?
-------------------------
Create an [issue on Github](https://github.com/piplongrun/TrailerAddict.bundle/issues) and add as much information as possible:
 - Plex Media Server version
 - Primary agent and order of any secondary agents
 - Log files, `com.plexapp.agents.traileraddict.log`

-
<img src="https://raw.githubusercontent.com/piplongrun/TrailerAddict.bundle/master/Contents/Resources/icon-default.jpg" width="150">
