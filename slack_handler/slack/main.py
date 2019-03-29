# Copyright 2018, Google, LLC.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START functions_slack_setup]
import json
from flask import jsonify
import requests
import re

with open('config.json', 'r') as f:
    data = f.read()
config = json.loads(data)

# [END functions_slack_setup]


# [START functions_verify_webhook]
def verify_web_hook(form):
    if not form or form.get('token') != config['SLACK_TOKEN']:
        raise ValueError('Invalid request/credentials.')
# [END functions_verify_webhook]


# [START functions_slack_format]
def format_slack_message(query, response):
    entity = None
    if response and response.get('itemListElement') is not None and \
       len(response['itemListElement']) > 0:
        entity = response['itemListElement'][0]['result']

    message = {
        'response_type': 'in_channel',
        'text': 'Query: {}'.format(query),
        'attachments': []
    }

    attachment = {}
    if entity:
        name = entity.get('name', '')
        description = entity.get('description', '')
        detailed_desc = entity.get('detailedDescription', {})
        url = detailed_desc.get('url')
        article = detailed_desc.get('articleBody')
        image_url = entity.get('image', {}).get('contentUrl')

        attachment['color'] = '#3367d6'
        if name and description:
            attachment['title'] = '{}: {}'.format(entity["name"],
                                                  entity["description"])
        elif name:
            attachment['title'] = name
        if url:
            attachment['title_link'] = url
        if article:
            attachment['text'] = article
        if image_url:
            attachment['image_url'] = image_url
    else:
        attachment['text'] = 'No results match your query.'
    message['attachments'].append(attachment)

    return message
# [END functions_slack_format]


def handle_request(form):
    endpoint = config["API_URL"]
    message = {
        "response_type": "in_channel",
        "text": "invalid command"
    }
    key = config["API_KEY"]
    headers = {"api-key": key}
    user1 = form.get("user_id")
    text_list = form["text"].split()
    if not text_list:
        return message
    cmd = text_list[0]
    player_regex = re.compile(r"(?<=<@)U\w+(?=|\w+>)")

    if cmd == "game":
        user2, score1, score2 = text_list[1:]
        score1, score2 = int(score1), int(score2)
        user2 = player_regex.search(user2).group()
        # create new user if not exist
        for u in user1, user2:
            requests.post(endpoint + "/player", data={"name": u},
                    headers=headers)
        data = {
                "p1_name": user1,
                "p2_name": user2,
                "p1_score": score1,
                "p2_score": score2
                }
        r = requests.post(endpoint + "/add-result", data=data, headers=headers)
        success = r.status_code == 200
        message["text"] = "Game recorded" if success else "Error recording game"
    elif cmd == "leaderboard":
        r = requests.get(endpoint + "/player", headers=headers)
        message["text"] = r.text if r.status_code == 200 else "problem fetching data"
    elif cmd == "history":
        r = requests.get(endpoint + "/match-history", headers=headers)
        message["text"] = r.text if r.status_code == 200 else "problem fetching data"
    elif cmd == "rating":
        if len(text_list) > 1:
            m = player_regex.search(text_list[1])
            if m:
                user1= m.group()
        r = requests.get(endpoint + f"/player/rating/{user1}", headers=headers)
        message["text"] = r.text if r.status_code == 200 else "problem fetching data"
    return message


# [START functions_slack_search]
def slack_handler(request):
    if request.method != 'POST':
        return 'Only POST requests are accepted', 405

    verify_web_hook(request.form)
    return jsonify(handle_request(request.form))
# [END functions_slack_search]

