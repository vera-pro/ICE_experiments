import requests
def wat_wiki_id(title):
    wat_url = 'https://wat.d4science.org/wat/title'
    payload = [("gcube-token", '5155a280-dfd5-421b-bd0b-748b2d7117a9-843339462'),
               ("title", title.replace(' ', '_')) ]

    response = requests.get(wat_url, params=payload)
    return response.json()['wiki_id']

import pickle
def wat_relatedness_pairwise(id1, id2, measure='w2v'):
    # Checking cache first
    try:
        relatedness_cache = pickle.load(open('/home/vprovat/EL_pickles/relatedness_cache.p', 'rb'))
        # storing WAT's relatedness values to avoid sending too many queries
    except:
        relatedness_cache = {}

    if measure in relatedness_cache:
        if id1 in relatedness_cache[measure]:
            if id2 in relatedness_cache[measure][id1]:
                return relatedness_cache[measure][id1][id2]
    '''
    Takes a list of Wiki IDs, returns pairwise similarities
    '''
    wat_url = 'https://wat.d4science.org/wat/relatedness/graph?'
    payload = [("gcube-token", '5155a280-dfd5-421b-bd0b-748b2d7117a9-843339462'),
              ('relatedness', measure)] + [("ids", str(pg_id)) for pg_id in [id1, id2]]

    response = requests.get(wat_url, params=payload)
    try:
        res = response.json()['pairs'][0]['relatedness']
    except:
        print('Fuck')
        print(id1, id2)
        print(response.json())
        return 0

    # Saving to cache
    if measure not in relatedness_cache:
        relatedness_cache[measure] = {}
    if id1 not in relatedness_cache[measure]:
        relatedness_cache[measure][id1] = {}
    if id2 not in relatedness_cache[measure]:
        relatedness_cache[measure][id2] = {}
    relatedness_cache[measure][id1][id2] = res
    relatedness_cache[measure][id2][id1] = res
    pickle.dump(relatedness_cache, open('/home/vprovat/EL_pickles/relatedness_cache.p', 'wb'))

    return res

import time
import json
def tagme_get_all_entities(utterance, tagmeToken='5155a280-dfd5-421b-bd0b-748b2d7117a9-843339462'):  # =tagmeToken):
    '''
    Returns all entities found with TagMe
    '''
    request_successfull = False
    cnt = 0
    while not request_successfull and cnt < 6:
        cnt += 1
        try:
            results = json.loads(requests.get(
                'https://tagme.d4science.org/tagme/tag?lang=en&gcube-token=' + tagmeToken + '&text=' + utterance).content)
            request_successfull = True
        except:
            print(utterance)
            time.sleep(5)

    if cnt == 6:
        return []
    # parse mentions
    mentions = []
    for mention in results['annotations']:
        mentions.append(mention['spot'])
    return mentions