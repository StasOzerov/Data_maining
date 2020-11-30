
from pathlib import Path
import json
import requests
import time


class Parse5ka:
    """
    Класс-парсер акционных товаров с сайта магазина Пятёрочка.
    Создает директорию data_parsed в той же директории где и исполняемый скрипт.
    В data_parsed записываются товары в формате f'{product["id"]}.json',
    где product["id"] это уникальный ID товара.
    Пример кода для запуска парсера:
        url = 'https://5ka.ru/api/v2/special_offers'
        parse5ka = Parse5ka(url)
        parse5ka.run()
    """

    _headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0",
    }

    _params = {
        'record_per_page': 50,
    }

    def __init__(self, start_url):
        self.start_url = start_url

    def parse(self, url):
        params = self._params
        while url:
            response: requests.Response = self._get(url, params=params, headers=self._headers)
            if params:
                params = {}
            data: dict = response.json()
            url = data.get('next')
            yield data.get('results')

    def run(self):
        for products in self.parse(self.start_url):
            for product in products:
                self._save_to_file(product)
            time.sleep(0.1)

    @staticmethod
    def _save_to_file(product, file_name=''):
        folder = Path('data_parsed')
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
        if file_name:
            fn = f'{file_name}.json'
        else:
            fn = f'{product["id"]}.json'
        filepath = folder / fn
        with open(filepath, 'w', encoding='UTF-8') as file:
            json.dump(product, file, ensure_ascii=False)

    @staticmethod
    def access(status_code):
        if status_code == 200:
            print('200: Request is OK! Data is accessable.')
            return True
        else:
            if status_code < 200:
                print('1xx: Informational')
            if status_code == 204:
                print('204: No content')
            if status_code == 206:
                print('206: Partial content')
            if status_code >= 300 and status_code < 400:
                print('3xx: Redirection')
            if status_code >= 400 and status_code < 500:
                print('4xx: Client Error')
            if status_code >= 500:
                print('5xx: Server Error')
            return False

    def _get(self, *args, **kwargs):
        while True:
            response = requests.get(*args, **kwargs)
            if self.access(response.status_code) is True:
                return response
            time.sleep(0.25)


class ParserCatalog(Parse5ka):
    """
    Дочерний класс к классу-парсеру акционных товаров с сайта магазина Пятёрочка.
    Создает директорию data_parsed в той же директории где и исполняемый скрипт.
    В data_parsed записываются товары по категориам в формате f'{file_name}.json',
    где file_name - это код категории товара.
    Пример кода для запуска парсера:
        url = 'https://5ka.ru/api/v2/special_offers'
        cat_url = 'https://5ka.ru/api/v2/categories'
        parserCatalog = ParserCatalog(url, cat_url)
        parserCatalog.run()
    """

    def __init__(self, start_url, category_url):
        self.category_url = category_url
        super().__init__(start_url)

    def get_cat(self, url):
        response = self._get(url, headers=self._headers)
        return response.json()

    def run(self):
        for cat in self.get_cat(self.category_url):
            data = {
                'name': cat['parent_group_name'],
                'code': cat['parent_group_code'],
                'products': []
            }

            self._params['categories'] = cat['parent_group_code']

            for products in self.parse(self.start_url):
                data['products'].extend(products)

            self._save_to_file(data, cat['parent_group_code'])


if __name__ == '__main__':
    url = 'https://5ka.ru/api/v2/special_offers'
    cat_url = 'https://5ka.ru/api/v2/categories'
    parser = ParserCatalog(url, cat_url)
    parser.run()
