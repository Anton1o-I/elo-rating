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

with open('config.json', 'r') as f:
    data = f.read()
config = json.loads(data)

# [END functions_slack_setup]


# [START functions_verify_webhook]
def verify_web_hook(form):
    if not form or form.get('token') != config['SLACK_TOKEN']:
        raise ValueError('Invalid request/credentials.')
# [END functions_verify_webhook]



def handle_request(form):
    endpoint = config["API_URL"]
    message = {
        "response_type": "in_channel",
        "text": "invalid command"
    }
    key = config["API_KEY"]
    headers = {"api-key": key}
    user1 = form.get("user_name")
    text_list = form["text"].split()
    if not text_list:
        return message
    cmd = text_list[0]

    if cmd == "game":
        user2, score1, score2 = text_list[1:]
        score1, score2 = int(score1), int(score2)
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
            user1 = text_list[1]
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

