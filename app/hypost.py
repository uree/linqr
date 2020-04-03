# -*- coding: utf-8 -*-
# python 3.6.9

import requests
import json
import logging
from keys import *

logger = logging.getLogger('app.hypost')


headers = {'Authorization': 'Bearer '+hypo_api_token, 'Accept': 'application/json'}


def hypost(citation_url, citation, twoway=False, src_url=None, tooltip_id=None):
    global headers
    global hypo_account
    logger.info("--- inint hypost ---")
    citation_dict = dict({"exact": citation, "type":"TextQuoteSelector"})
    citation_dict_list = []
    citation_dict_list.append(citation_dict)


    if twoway:
        text = "Discussed [here]("+src_url+"#"+tooltip_id+").\n This annotation was generated automatically by [Linqr](https://yurisearch.coventry.ac.uk/linqr/about)."
    else:
        text = "This annotation was generated automatically by [Linqr](https://yurisearch.coventry.ac.uk/linqr/about)."


    tags = ["linqr"]


    #authentication request
    api_url = "https://hypothes.is/api/"


    #constructing post
    post_data = {

        "group": "__world__",
        "permissions": {
            "admin": [
                hypo_account
            ],
            "delete": [
                hypo_account
            ],
            "read": [
                "group:__world__"
            ],
            "update": [
                hypo_account
            ]
        },
        "references": [],

        "tags": [],
        "target": [
                {
                    "selector": []
                }
            ],
        "text": "",
        "uri": ""

        }


    # reconfigure this
    post_data['tags'] = tags
    post_data['text'] = text
    post_data['uri'] = citation_url
    post_data['target'][0]['selector'] = citation_dict_list


    #posting
    try:
        post_annot = requests.post('https://hypothes.is/api/annotations', headers=headers, json=post_data)
    except Exception as e:
        logger.error("Error posting to hypothes.is")

    return post_annot.json()


def hyposearch(user, hits):
    global headers
    search = requests.get('https://hypothes.is/api/search?limit=1000&user='+user, headers=headers)

    results_json = json.loads(search.text)

    return json.dumps(results_json['rows'][0:hits], indent=4, sort_keys=True)


def hypodelete(ID):
    global headers
    delete = requests.delete('https://hypothes.is/api/annotations/'+ID, headers=headers)
    return delete.json()


# if __name__ == '__main__':
#     #hypost(href, quote, linkback=False)
#     ids = ['qfZREG5xEeqLRnPMYM138Q']
#     for i in ids:
#         print(hypodelete(i))
