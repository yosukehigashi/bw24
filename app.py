import base64
import io
import json
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
                  [
                      img['src'].replace('medium', 'large')
                      for img in soup.find_all('img')
                  ])
    dirs = list(dict.fromkeys(dirs))

    r = requests.get(url)
    if r.status_code != 200:
        return None, []

    soup = BeautifulSoup(r.text, 'html.parser')

    title = soup.find('h2', {'class': 'text-xl'}).text

    return title, [
        "https://www.instabase.jp" + directory for directory in list(dirs)
    ]


def function_call_prompt(long_text: str) -> str:
    return f'''
    The following text describes three calls to a
    `search_and_replace(search_prompt, replace_prompt)` function.:
    ************
    [Text]: {long_text}
    ************

    Call the function `search_and_replace_all(search_prompts, replace_prompts)`,
    where `search_prompts` is the list of the three search prompts and
    `replace_prompts` is the list of the three corresponding replace prompts.
    '''


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
            }]
        }],
        max_tokens=2000)
    description = response.choices[0].message.content
    print(description)

    # Call the GPT-4-Turbo model using function calling to get a structured
    # response
    fn_call_messages = [{
        "role": "user",
        "content": function_call_prompt(description)
    }]
    functions = [{
        "name": 'search_and_replace_all',
        "description": 'Applies search and replace edits to an image',
        "parameters": {
            "type": "object",
            "properties": {
                'search_prompts': {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": 'List of three search prompts',
                },
                'replace_prompts': {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": 'List of three replace prompts',
                }
            },
            "required": ['search_prompts', 'replace_prompts'],
        }
    }]
    response = client.chat.completions.create(
        model='gpt-4',
        messages=fn_call_messages,
        seed=42,
        functions=functions,
        function_call={"name": 'search_and_replace_all'})
    # For type checking
    assert response.choices[0].message.function_call is not None
    function_args = json.loads(
        response.choices[0].message.function_call.arguments)
    search_prompts = function_args.get('search_prompts')
    replace_prompts = function_args.get('replace_prompts')
    assert search_prompts is not None
    assert replace_prompts is not None
    assert len(search_prompts) == 3
    assert len(replace_prompts) == 3
    return search_prompts, replace_prompts


def send_generation_request(host, params, image):
    headers = {
        "Accept": "image/*",
        "Authorization": f"Bearer {stability_ai_api_key}"
    }

    # Encode parameters
    files = {'image': image}

    # Send request
    print(f"Sending REST request to {host}...")
    response = requests.post(host, headers=headers, files=files, data=params)
    if not response.ok:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

    return response


def edit_single_image(input_image, prompt, search_prompt):
    host = f"https://api.stability.ai/v2beta/stable-image/edit/search-and-replace"
    negative_prompt = ""
    seed = 0
    output_format = "webp"
    params = {
        "seed": seed,
        "mode": "search",
        "output_format": output_format,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "search_prompt": search_prompt,
    }
    response = send_generation_request(host, params, input_image)
    # Decode response
    output_image = response.content
    finish_reason = response.headers.get("finish-reason")
    seed = response.headers.get("seed")

    # Check for NSFW classification
    if finish_reason == 'CONTENT_FILTERED':
        raise Warning("Generation failed NSFW classifier")

    # Save result for debugging
    edited = f"edited_{seed}.{output_format}"
    with open(edited, "wb") as f:
        f.write(output_image)
    return output_image


@app.route('/venue/<venueid>', methods=['GET'])
def venue(venueid):
    title, urls = scrape_listing(venueid)
    return {'title': title, 'urls': urls[:3]}


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    original_image = request.json['images']
    trend = request.json['trend']
    search_prompts, replace_prompts = get_search_and_replace_prompts(
        trend, original_image)
    print(f'Search prompts: {search_prompts}')
    print(f'Replace prompts: {replace_prompts}')

    edited_image = edit_single_image(
        base64.decodebytes(bytes(original_image, 'utf-8')), replace_prompts[0],
        search_prompts[0])

    return {'image': base64.b64encode(edited_image).decode('utf-8')}


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
        })

    if response.status_code != 200:
        print(str(response.text))
        return None

    # with open("out.jpeg", "wb") as fd:
    #     fd.write(response.content)

    return {'image': base64.b64encode(response.content).decode('utf-8')}


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
