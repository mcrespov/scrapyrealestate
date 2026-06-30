import scrapy


class ScrapyrealestateItem(scrapy.Item):
    id = scrapy.Field()
    price = scrapy.Field()
    m2 = scrapy.Field()
    rooms = scrapy.Field()
    floor = scrapy.Field()
    town = scrapy.Field()
    neighbour = scrapy.Field()
    street = scrapy.Field()
    number = scrapy.Field()
    type = scrapy.Field()
    title = scrapy.Field()
    href = scrapy.Field()
    site = scrapy.Field()
    post_time = scrapy.Field()
