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



# [START functions_slack_search]
def slack_handler(request):
    if request.method != 'POST':
        return 'Only POST requests are accepted', 405

    verify_web_hook(request.form)
    api_response = requests.post()
    return jsonify({"text": "hello world"})
# [END functions_slack_search]

