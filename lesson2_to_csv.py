
import requests
import bs4
import time
from urllib.parse import urljoin
import datetime as dt
import csv


class MagnitParse:
    """
    Класс запускает парсинг данных сайта магазина 'Магнит' раздела 'Акции и спецпредложения'.
    Используемый url: 'https://magnit.ru/promo/?geo=moskva'.
    Пример кода для запуска парсера:
        url = 'https://magnit.ru/promo/?geo=moskva'
        path = 'magnit.csv'
        parser = MagnitParse(url, path)
        parser.run()
    """

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:83.0) Gecko/20100101 Firefox/83.0'
    }

    def __init__(self, start_url, path):
        self.start_url = start_url
        self.path = path
        self.product_template = {
            'url': lambda soup: urljoin(start_url, soup.get('href')),
            'image_url': lambda soup: urljoin(start_url, soup.find('img').get('data-src')),

            'promo_name': lambda soup: soup.find('div', attrs={'class': 'card-sale__header'}).text,
            'product_name': lambda soup: soup.find('div', attrs={'class': 'card-sale__title'}).text,

            'old_price': lambda soup: self.get_price(
                soup.find('div', attrs={'class': 'label__price_old'}).text),
            'new_price': lambda soup: self.get_price(
                soup.find('div', attrs={'class': 'label__price_new'}).text),

            'date_from': lambda soup: self.get_date(
                soup.find('div', attrs={'class': 'card-sale__date'}).text[1:-1], 'from'),
            'date_to': lambda soup: self.get_date(
                soup.find('div', attrs={'class': 'card-sale__date'}).text[1:-1], 'to'),
        }

    @staticmethod
    def get_price(price: str) -> str:
        price = price[1:-1]
        if '\n' in price:
            return price[:price.find('\n')] + '.' + price[price.find('\n') + 1:]
        if '%' in price:
            return price[1:] + ' скидка'
        return price

    @staticmethod
    def get_month(date: str) -> str:
        months = {
            '12': 'дек', '01': 'янв', '02': 'фев',
            '03': 'март', '04': 'апр', '05': 'мая',
            '06': 'июн', '07': 'июл', '08': 'авг',
            '09': 'сен', '10': 'окт', '11': 'ноя',
        }
        for key, value in months.items():
            if value in date:
                return key

    def get_date(self, date, from_or_to):
        date_from = date[2:date.find('\n')]
        month_from = self.get_month(date_from)
        date_from = date_from[:2] + f'/{month_from}/'

        date_to = date[date.find('\n') + 4:]
        month_to = self.get_month(date_to)
        date_to = date_to[:2] + f'/{month_to}/'

        date_from += str(dt.datetime.now().year)
        if int(month_from) <= int(month_to):
            date_to += str(dt.datetime.now().year)
        else:
            date_to += str(dt.datetime.now().year + 1)
        if from_or_to == 'from':
            return date_from
        if from_or_to == 'to':
            return date_to
        return 'xx/xx/xxxx'

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
            if 300 <= status_code < 400:
                print('3xx: Redirection')
            if 400 <= status_code < 500:
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

    def soup(self, url) -> bs4.BeautifulSoup:
        response = self._get(url, headers=self.headers)
        return bs4.BeautifulSoup(response.text, 'lxml')

    def run(self):
        soup = self.soup(self.start_url)
        self.table_header()
        for product in self.parse(soup):
            self.save(product)

    def parse(self, soup):
        catalog = soup.find('div', attrs={'class': 'сatalogue__main'})
        for product in catalog.find_all('a', recursive=False):
            pr_data = self.get_product(product)
            yield pr_data

    def get_product(self, product_soup) -> dict:
        result = {}
        for key, value in self.product_template.items():
            try:
                result[key] = value(product_soup)
            except AttributeError:
                result[key] = None
        return result

    def table_header(self):
        with open(self.path, 'w', newline='', encoding='cp1251') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(self.product_template.keys())

    def save(self, product):
        with open(self.path, 'a', newline='', encoding='cp1251') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow([product['url'], product['image_url'],
                             product['promo_name'], product['product_name'],
                             product['old_price'], product['new_price'],
                             product['date_from'], product['date_to']])


if __name__ == '__main__':
    parser = MagnitParse('https://magnit.ru/promo/?geo=moskva', 'magnit.csv')
    parser.run()
