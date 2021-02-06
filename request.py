import requests
from bs4 import BeautifulSoup
import sqlite3

wiki_links = []
railway_stations = []

conn = sqlite3.connect('database.db')
c = conn.cursor()


def get_href_links(main_url):
    website_url = requests.get(url=main_url)

    soup = BeautifulSoup(website_url.content, 'html.parser')

    my_list = soup.find('table', {'class': 'nowraplinks hlist navbox-inner'})
    #    print(my_list)

    for a in my_list.find_all('a', href=True):
        str = "https://en.wikipedia.org" + a.get('href')
        wiki_links.append(str)


def scrapeWikiArticle(url):
    website_url = requests.get(url=url)

    soup = BeautifulSoup(website_url.content, 'html.parser')
    # print(soup.prettify())

    my_table = soup.find('table', {'class': 'wikitable'})
    # print(my_table)

    rows = my_table.findChildren('tr')
    # print(rows)

    for row in rows:
        links = row.findChildren('a')  # get href tag
        for link in links:
            name = link.get('title')
            if (name == None or "station" not in name):
                continue
            else:
                railway_stations.append(link.text)


if __name__ == '__main__':
    """ ======== Unit testing ========
    print(">> Unit test for get_href_links(main_url) method")
    print("main_url.. https://en.wikipedia.org/wiki/UK_railway_stations")

    get_href_links("https://en.wikipedia.org/wiki/UK_railway_stations")
    print("Individual links.. ")
    for link in wiki_links:
        print(link)
        scrapeWikiArticle(link)
    print(">> Unit test for scrapeWikiArticle(link) method")
    print("Extracting railway station names from each link.. ")
    print("UK railways stations: ")
    for stations in railway_stations:
        print(stations)
        ''' -- Uncomment to fill in Database --
        c.execute('INSERT INTO railway_stations VALUES(?)', (stations,))
        conn.commit()
        '''
    """
