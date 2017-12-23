from podcastController import PodcastController

pc = PodcastController()
feeds = pc.get_feeds()
print(feeds)

