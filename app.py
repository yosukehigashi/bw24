import base64
import io
import os
import random

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, make_response, request, send_file
from flask_cors import CORS
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
CORS(app)

stability_ai_api_host = "https://api.stability.ai"
stability_ai_api_key = os.getenv("STABILITY_AI_API_KEY")

engine_id = "esrgan-v1-x2plus"

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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


def get_search_and_replace_prompts(trend, image):
    prompt = f"""
    You are an AI that has the function
    `search_and_replace(search_prompt, replace_prompt)`. The function operates
    as follows:
    - search for the object or item specified in `search_prompt`
    - generate a segmentation mask around the identified object or item
    - inpaint the masked area with the prompt `replace_prompt`
    
    Output three calls to `search_and_replace(search_prompt, replace_prompt)`
    that would make this venue look more like a {trend}.
    """

    # Call the GPT-4V model
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "system",
            "content": "You are a helpful assistant."
        }, {
            "role":
                "user",
            "content": [{
                "type": "text",
                "text": prompt
            }, {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image}"
                }
            }
            ]
        }],
        max_tokens=2000)
    description = response.choices[0].message.content
    print(description)

@app.route('/venue/<venueid>', methods=['GET'])
def venue(venueid):
    title, urls = scrape_listing(venueid)
    return {'title': title, 'urls': urls[:3]}


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    original_image = request.json['images']
    trend = request.json['trend']
    get_search_and_replace_prompts(trend, original_image)
    response = requests.post(
        f"{stability_ai_api_host}/v1/generation/{engine_id}/image-to-image/upscale",
        headers={
            "Accept": "image/png",
            "Authorization": f"Bearer {stability_ai_api_key}"
        },
        files={
            "image": base64.decodebytes(bytes(original_image, 'utf-8'))
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
