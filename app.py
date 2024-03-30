from flask import Flask
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)


def scrape_listing(room_id):
    url = "https://www.instabase.jp" + "/space/" + str(room_id)

    r = requests.get(url + "/images")
    if r.status_code != 200:
        return None, []

    soup = BeautifulSoup(r.text, 'html.parser')

    dirs = filter(lambda x: x.startswith("/imgs/r/uploads/room_image/image/"),
                  [img['src'].replace('medium', 'large') for img in soup.find_all('img')])
    dirs = list(dict.fromkeys(dirs))

    r = requests.get(url)
    if r.status_code != 200:
        return None, []

    soup = BeautifulSoup(r.text, 'html.parser')

    title = soup.find('h2', {'class': 'text-xl'}).text

    return title, [url + directory for directory in list(dirs)]


@app.route('/venue', methods=['GET'])
def venue():
    return {'dummy_id': 1}


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
