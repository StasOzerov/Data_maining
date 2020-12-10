import scrapy
import pymongo



class AutoyoulaSpider(scrapy.Spider):
    name = 'autoyoula'
    allowed_domains = ['auto.youla.ru']  # domain control
    start_urls = ['http://auto.youla.ru/']

    css_query = {
        'brands': '.ColumnItemList_container__5gTrc .ColumnItemList_column__5gjdt a.blackLink',
        'pagination': '.Paginator_block__2XAPy a.Paginator_button__u1e7D',
        'ads': 'article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_name__3F7Yu',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = pymongo.MongoClient()['parse_gb_11'][self.name]

    def parse(self, response):
        for brand in response.css(self.css_query['brands']):
            yield response.follow(brand.attrib.get('href'), callback=self.brand_page_parse)

    def brand_page_parse(self, response):
        for pag_page in response.css(self.css_query['pagination']):
            yield response.follow(pag_page.attrib.get('href'), callback=self.brand_page_parse)

        for ads_page in response.css(self.css_query['ads']):
            yield response.follow(ads_page.attrib.get('href'), callback=self.ads_parse)

    def ads_parse(self, response):
        data = {
            'title': response.css('div.AdvertCard_advertTitle__1S1Ak::text').get(),
            'images': [img.attrib.get('src') for img in response.css('figure.PhotoGallery_photo__36e_r img')],
            'description': response.css('.AdvertCard_descriptionInner__KnuRi::text').get(),
            'url': response.url,
            'author': '',
            'specification': self.get_spec(response),

        }

        self.db.insert_one(data)

    def get_spec(self, response):
        return {
            item.css('.AdvertSpecs_label__2JHnS').get():
                item.css('.AdvertSpecs_data__xK2Qx::text').get() or item.css('a::text').get() for item in
                    response.css('.AdvertSpecs_row__ljPcX')
        }

