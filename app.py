import base64
import io
import os
import random

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, make_response, request, send_file
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

stability_ai_api_host = "https://api.stability.ai"
stability_ai_api_key = os.getenv("STABILITY_AI_API_KEY")

engine_id = "esrgan-v1-x2plus"


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

    return title, ["https://www.instabase.jp" + directory for directory in list(dirs)]


@app.route('/venue/<venueid>', methods=['GET'])
def venue(venueid):
    title, urls = scrape_listing(venueid)
    return {'title': title, 'urls': urls[:3]}


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    trend = request.json['trend']
    response = requests.post(
        f"{stability_ai_api_host}/v1/generation/{engine_id}/image-to-image/upscale",
        headers={
            "Accept": "image/png",
            "Authorization": f"Bearer {stability_ai_api_key}"
        },
        files={
            "image": base64.decodebytes(bytes(request.json['images'], 'utf-8'))
        },
        data={
            "width": 1024,
        }
    )

    if response.status_code != 200:
        print(str(response.text))
        return None

    with open("out.jpeg", "wb") as fd:
        fd.write(response.content)

    return {'image': base64.b64encode(response.content).decode('utf-8')}


@app.route('/upscale', methods=['GET', 'POST'])
def upscale():
    response = requests.post(
        f"{stability_ai_api_host}/v1/generation/{engine_id}/image-to-image/upscale",
        headers={
            "Accept": "image/png",
            "Authorization": f"Bearer {stability_ai_api_key}"
        },
        files={
            "image": base64.decodebytes(bytes(request.json['images'], 'utf-8'))
        },
        data={
            "width": 1024,
        }
    )

    if response.status_code != 200:
        print(str(response.text))
        return None

    # with open("out.jpeg", "wb") as fd:
    #     fd.write(response.content)

    return {'image': base64.b64encode(response.content).decode('utf-8')}


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
