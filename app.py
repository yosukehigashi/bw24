import asyncio
import base64
import io
import json
import os
import random

import httpx
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, make_response, request, send_file
from flask_cors import CORS
from openai import OpenAI
from PIL import Image

from autocamper import generate_campaign

from autocamper import generate_campaign

load_dotenv()

app = Flask(__name__)
CORS(app)

stability_ai_api_host = "https://api.stability.ai"
stability_ai_api_key = os.getenv("STABILITY_AI_API_KEY")

engine_id = "esrgan-v1-x2plus"

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


ib_trends = [
    "Meetings",
    "Dance",
    "Seminars",
    "Workouts",
    "Massages",
    "Teleworking",
    "Home Party",
    "Pizza Party",
]


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

    div = soup.find_all('div', {'class': 'mt-6'})[2]
    tags = [i.text for i in div.find_all('button')]

    return title, [
        "https://www.instabase.jp" + directory for directory in list(dirs)
    ], tags


def search_and_replace_function_call_prompt(long_text: str) -> str:
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
        "role":
        "user",
        "content":
        search_and_replace_function_call_prompt(description)
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
        model='gpt-3.5-turbo',
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


def encode_image_bytes(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')


def downscale_image(image_base64, scale_factor):
    # Convert the base64 string to a PIL image
    img_data = base64.b64decode(image_base64)
    img = Image.open(io.BytesIO(img_data))

    # Calculate the new size
    width, height = img.size
    new_size = (int(width * scale_factor), int(height * scale_factor))

    # Resize the image
    img_resized = img.resize(new_size, Image.Resampling.LANCZOS)

    # Convert the image to RGB if it's RGBA
    if img_resized.mode == 'RGBA':
        img_resized = img_resized.convert('RGB')

    # Convert the PIL image back to a base64 string
    buffered = io.BytesIO()
    img_resized.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return img_str


async def send_generation_request_async(host, params, image):
    headers = {
        "Accept": "image/*",
        "Authorization": f"Bearer {stability_ai_api_key}"
    }

    # Encode parameters
    files = {'image': image}

    # Send request
    print(f"Sending REST request to {host}...")
    timeout = httpx.Timeout(30.0, connect=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(host,
                                     headers=headers,
                                     files=files,
                                     data=params)
        if not response.is_success:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        return response


async def edit_single_image(input_image, prompt, search_prompt):
    host = "https://api.stability.ai/v2beta/stable-image/edit/search-and-replace"
    negative_prompt = ""
    seed = 0
    output_format = "jpeg"
    params = {
        "seed": seed,
        "mode": "search",
        "output_format": output_format,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "search_prompt": search_prompt,
    }
    response = await send_generation_request_async(host, params, input_image)
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


def select_best_image_function_call_prompt(long_text, available_image_names,
                                           trend) -> str:
    return f'''
    The following is an assessment of which edited image is the most appropriate
    for depicting the a venue being used for a {trend}:
    ************
    [Text]: {long_text}
    ************

    Save the best edited image. The available input image names are:
    {available_image_names}
    '''


def select_best_image(original_image, edited_dict, trend):
    user_prompt = f"""
    You are an expert at assessing the quality of edited images. The first image
    is the original image of the venue (`original_image`), and the subsequent
    images are edited images (`edited_image_1`, `edited_image_2`, etc.) that are
    intended to show the venue being used for a {trend}.

    Determine which edited image is the most appropriate. Consider factors such as
    the general quality of the image and how realistic it looks, whether it is a
    realistic edit of the original image, and whether it convincingly looks like the
    venue is being used for a {trend}.

    After explaining your reasoning, specify which edited image is the best choice.
    Remember that the first image is the original image, the second image is
    `edited_image_1`, the third image is `edited_image_2`, etc.
    """

    images_list = [{
        "type": "image_url",
        "image_url": {
            "url":
            f"data:image/jpeg;base64,{downscale_image(original_image, 0.25)}"
        }
    }]
    for _, edited_image in edited_dict.items():
        images_list.append({
            "type": "image_url",
            "image_url": {
                "url":
                f"data:image/jpeg;base64,{downscale_image(encode_image_bytes(edited_image), 0.25)}"
            }
        })
    print(f'Evaluating the best out of {len(edited_dict)} images...')
    content = [{"type": "text", "text": user_prompt}] + images_list
    # Call the GPT-4V model
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "system",
            "content": "You are a helpful assistant."
        }, {
            "role": "user",
            "content": content
        }])
    description = response.choices[0].message.content
    print(description)

    # Call the GPT-4-Turbo model using function calling to get a structured
    # response
    available_image_names = [
        f"edited_image_{i}" for i in range(1,
                                           len(edited_dict) + 1)
    ]
    fn_call_messages = [{
        "role":
        "user",
        "content":
        select_best_image_function_call_prompt(description,
                                               available_image_names, trend)
    }]
    functions = [{
        "name": 'save_best_edited_image',
        "description": 'Saves the best edited image',
        "parameters": {
            "type": "object",
            "properties": {
                'edited_image_name': {
                    "type": "string",
                    "enum": available_image_names,
                    "description": 'Best edited image',
                },
            },
            "required": ['edited_image_name'],
        },
    }]
    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=fn_call_messages,
        seed=42,
        functions=functions,
        function_call={"name": 'save_best_edited_image'})
    # For type checking
    assert response.choices[0].message.function_call is not None
    function_args = json.loads(
        response.choices[0].message.function_call.arguments)
    assessment = function_args.get('edited_image_name')
    assert assessment is not None
    # Return the image in edited_dict that corresponds to the best assessment
    index = available_image_names.index(assessment)
    key = list(edited_dict.keys())[index]
    print(
        f'Selected the best image {assessment} that corresponds to the edit with key {key}'
    )
    return edited_dict[key]


def select_relevant_trends(trends, image_url):
    user_prompt = f"""
    You are an expert at assessing whether the following events: {trends} could be hosted at a venue. You will be given 
    an image of the venue. For each possible event, you are to explain why that event could or could not be hosted
    at the given venue and return an updated version of the possible events list without the events that shouldn't be 
    hosted there. The last line of input should only be the comma separated list of possible events.
    """

    image = [{
        "type": "image_url",
        "image_url": {
            "url":
                image_url
        }
    }]

    print(f'Starting to check viability of trends for venue')
    content = [{"type": "text", "text": user_prompt}] + image
    # Call the GPT-4V model
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "system",
            "content": "You are a helpful assistant."
        }, {
            "role": "user",
            "content": content
        }])
    description = response.choices[0].message.content
    print(description)

    return description.split('\n')[-1].replace("*", "").replace("\"", "").split(',')

    
def simple_prompt(prompt, sys_prompt="You are a helpful assistant."):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "system",
            "content": sys_prompt,
        }, {
            "role": "user",
            "content": prompt,
        }],
        max_tokens=100)

    print(response.choices[0].message)

    return response.choices[0].message


@app.route('/venue/<venueid>', methods=['GET'])
def venue(venueid):
    title, urls, tags = scrape_listing(venueid)

    return {'title': title, 'urls': urls[:3], 'tags': tags, 'trends': select_relevant_trends(ib_trends, urls[0])}


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    # This is a wrapper function to handle synchronous Flask route
    return asyncio.run(edit_async())


async def edit_async():
    original_image = request.json['images']
    trend = request.json['trend']
    search_prompts, replace_prompts = get_search_and_replace_prompts(
        trend, original_image)
    print(f'Search prompts: {search_prompts}')
    print(f'Replace prompts: {replace_prompts}')

    original_image_bytes = base64.decodebytes(bytes(original_image, 'utf-8'))

    # First round (prompt_0, prompt_1, prompt_2)
    first_round_tasks = [
        edit_single_image(original_image_bytes, rp, sp)
        for rp, sp in zip(replace_prompts, search_prompts)
    ]
    first_round_results = await asyncio.gather(*first_round_tasks)
    # Store first round results in edited_dict
    edited_dict = {
        f'{i}': result
        for i, result in enumerate(first_round_results)
    }

    # Second round (prompt_0 -> prompt_1, prompt_1 -> prompt_2, prompt_2 -> prompt_0)
    num_prompts = len(search_prompts)
    second_round_tasks = [
        edit_single_image(edited_dict[f'{i}'],
                          replace_prompts[(i + 1) % num_prompts],
                          search_prompts[(i + 1) % num_prompts])
        for i in range(num_prompts)
    ]
    second_round_results = await asyncio.gather(*second_round_tasks)
    # Store second round results in edited_dict
    for i, result in enumerate(second_round_results):
        edited_dict[f'{i}->{(i + 1) % num_prompts}'] = result

    # Select the best image
    best_edited_image = select_best_image(original_image, edited_dict, trend)

    return {'image': base64.b64encode(best_edited_image).decode('utf-8')}


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


@app.route('/gen-campaign')
def gen_campaign():
    ib_id = request.json['venueid']
    tags = request.json['tags']
    trend = request.json['trend']
    budget = request.json['budget']

    headlines = [hl[4:-1].replace("!", "") for hl in simple_prompt(
        f"""Please make 3 unique 4 word headlines to get people to click on my link based on the following data: 
                        {trend}, {tags}
                        """,
        "You are a search engine optimization assistant."
    ).content.split("\n")]

    descriptions = [hl[4:-1].replace("!", "") for hl in simple_prompt(
        f"""Please make 2 unique 15 word descriptions to get people to click on my link based on the following data:  
                        {trend}, {tags}
                        """,
        "You are a search engine optimization assistant."
    ).content.split("\n")]

    keywords = [hl[2:].replace("!", "") for hl in simple_prompt(
        f"""Generate 10 popular search keywords that would help google searches find my listing based on the following terms:  
                            {trend}, {tags}
                            """,
        "Output only the terms."
    ).content.split("\n")]

    generate_campaign(ib_id, budget, headlines, descriptions, keywords)

    return {"headlines": headlines, "descriptions": descriptions, "keywords": keywords}

  
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
