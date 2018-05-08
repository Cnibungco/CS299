import scrapy
import json
import re
import scrapy_crawlera
from pandas import Series, DataFrame

# response.css = css selector
# response.xpath = xpath selector (you can use the selector tool from Chrome to make this)
# response.urljoin(url) = start_urls + url (combining string)
# when using the SelectorGadget, pay attention what you are copying from. Look for the tag used when copying css code
# MAKE SURE YOU DECLARE THE VARIABLE "name" when initializing a spider. THIS IS VERY IMPORTANT
# for some reason this link works https://www.whosampled.com/J-Dilla/?role=2 but this link doesn't https://www.whosampled.com/J-Dilla/?role=2&ob=0
# scrapy needs a default parse method in order for it run, so your main parse method to continue parsing through website will be defined as def parse(self, response) any method after will be defined as another name

# Lists for DataFrame


class WhoSampledSpider(scrapy.Spider):
    name = 'WhoSampled'
    allowed_domains = ['whosampled.com']
    artist_url = 'https://www.whosampled.com/J-Dilla/?role=2&sp={}'
    start_urls = [artist_url.format(1)]


    # main parsing method to go through pages and initiate parseTrackURL method
    # this parse method paginates all links

    def __init__(self):
        self.sampleGenre = []
        self.sampleName = []
        self.trackName = []
        self.producerName = []

    def parse(self, response):

        # Get name of Producer
        # global producerName, trackName
        # producerName = response.css('div.artistDetails > h1.artistName::text').extract_first()

        # Creates List
        artistPageList = response.css('div.pagination > span.page > a::text').extract()
        artistPageList = [int(x) for x in artistPageList]
        maxPageNum = max(artistPageList)
        for i in range(0, maxPageNum):
            trackURL = response.css('h3.trackName > a::attr(href)').extract()
            # trackName = response.css('article.trackItem > header.trackItemHead > h3.trackName > a::attr(title)').extract()

            for traURL in trackURL:
                yield scrapy.Request(url='https://www.whosampled.com' + traURL, callback=self.parseTrackURL)
            pageNum = i + 1
            yield scrapy.Request(url=self.artist_url.format(pageNum), callback=self.parse)

    def parseTrackURL(self, response):
        # global producerName, trackName, sampleName, sampleGenre
        # Get string that says "Contains samples of x songs"
        numberOfSamples = response.css('span.section-header-title::text').extract_first()

        # use regex to get int in string
        numSamples = int(re.search(r'\d+', numberOfSamples).group())

        # for loop to grab sampleName and sampleGenre

        count = 0
        while (count < numSamples):
            samGenre = response.css('div.list.bordered-list > div.listEntry.sampleEntry > div.trackDetails > div.trackBadge > span.bottomItem::text')[count].extract()
            samGenre = samGenre.split(' / ')
            self.sampleGenre.append(samGenre)
            self.sampleName.append(response.css('div.list.bordered-list > div.listEntry.sampleEntry > div.trackDetails > div.details-inner > a::attr(title)')[count].extract())
            self.producerName.append(response.css('div.track-metainfo > h3 > span > span > a::text').extract())
            songName = response.css('div.trackInfo > h1::text').extract_first() + " by " + response.css('div.trackInfo > div.trackArtists > h2.h2-heading > a::text').extract_first()
            self.trackName.append(songName)
            count = count + 1

        self.createCSV(self.producerName, self.trackName, self.sampleName, self.sampleGenre)



    def createCSV(self, pName, tName, sName, sGenre):
        data = {'Producer': pName, 'Track Name': tName, 'Sample Name': sName, 'Sample Genre(s)': sGenre}
        df = DataFrame(data)
        df.set_index('Producer', inplace=True)
        df.to_csv("J Dilla.csv")
        return df