from REL.mention_detection import MentionDetection
from REL.ner import load_flair_ner
from REL.utils import process_results
from REL.entity_disambiguation import EntityDisambiguation
from utils_REL import *
wiki_version = "wiki_2019"
base_url = '/ivi/ilps/personal/vprovat/REL_files'

import requests
from utils import tagme_get_all_entities

import json
from collections import namedtuple

MentionEntry = namedtuple('MentionEntry', 'mention candidates')
CandidateEntry = namedtuple("CandidateEntry", 'candidate score')

def process_candidates(mentions_dataset, threshold=0.05):
    res = []
    for item in mentions_dataset:
        # print(item)
        cands = []
        for cand in item['candidates']:
            if cand[-1] > threshold:
                cands.append(CandidateEntry(cand[0], cand[-1]))
            else:
                break
        # print(cands)
        res.append(MentionEntry(item['mention'], cands))
    return res

import pickle

# def get_candidates_end2end():
#     tagger_ner = load_flair_ner("ner-fast")
#     top = json.load(open('ShadowLink/Top.json', 'r'))
#
#     entries_top = []
#     for entry in top:
#         gt_mention = entry['entity_space_name'].lower()
#         example = entry['example']
#         input_text = preprocess(example)
#         mentions_dataset, n_mentions = mention_detection.find_mentions(input_text, tagger_ner)
#         mentions_found = [item['mention'].lower() for item in mentions_dataset['test_doc1']]
#         if not gt_mention in mentions_found:
#             print('target entity not found:')
#             print(gt_mention)
#             print(example)
#             print(mentions_found)
#             print()
#             continue
#
#         cands_dataset = process_candidates(mentions_dataset['test_doc1'])
#         if len(cands_dataset) > 1:
#             entries_top.append(cands_dataset)
#
#     pickle.dump(entries_top, open('pickles/entries_top.p', 'wb'))

from tqdm.auto import tqdm
import json
if __name__ == '__main__':
    path_to_data = '/home/vprovat/EL_dataset/ShadowLink'
    shadow = json.load(open(path_to_data + '/Shadow.json', 'r'))
    top = json.load(open(path_to_data + '/Top.json', 'r'))

    entries_shadow_tagme = []  # ner by tagme, candidate retrieval by rel
    cnt = 0
    for item in tqdm(shadow):
        example = item['example']
        context_mentions = tagme_get_all_entities(example)
        spans = [[example.find(mention), len(mention)] for mention in context_mentions]
        found_target = False
        for ment in context_mentions:
            if item['entity_space_name'].lower() == ment.lower():
                found_target = True
                break
        if not found_target:
            spans.append([example.lower().find(item['entity_space_name'].lower()),
                          len(item['entity_space_name'])]
                         )

        entry = {"doc_1": [example, spans]}
        dataset = get_mentions_dataset(entry)
        cands_dataset = process_candidates(dataset['doc_1'])
        entries_shadow_tagme.append(cands_dataset)
        if cnt and cnt % 20 == 0:
            pickle.dump(entries_shadow_tagme, open('/home/vprovat/EL_pickles/entries_shadow_tagme.p', 'wb'))
            print(entries_shadow_tagme[-1])
        cnt += 1

    pickle.dump(entries_shadow_tagme, open('/home/vprovat/EL_pickles/entries_shadow_tagme.p', 'wb'))

    # entries_top_tagme = []  # ner by tagme, candidate retrieval by rel
    # cnt = 0
    # for item in tqdm(top):
    #     example = item['example']
    #     context_mentions = tagme_get_all_entities(example)
    #     spans = [[example.find(mention), len(mention)] for mention in context_mentions]
    #     found_target = False
    #     for ment in context_mentions:
    #         if item['entity_space_name'].lower() == ment.lower():
    #             found_target = True
    #             break
    #     if not found_target:
    #         spans.append([example.lower().find(item['entity_space_name'].lower()),
    #                       len(item['entity_space_name'])]
    #                      )
    #
    #     entry = {"doc_1": [example, spans]}
    #     dataset = get_mentions_dataset(entry)
    #     cands_dataset = process_candidates(dataset['doc_1'])
    #     entries_top_tagme.append(cands_dataset)
    #     if cnt and cnt % 20 == 0:
    #         pickle.dump(entries_top_tagme, open('/home/vprovat/EL_pickles/entries_top_tagme.p', 'wb'))
    #         print(entries_top_tagme[-1])
    #     cnt += 1
    #
    # pickle.dump(entries_top_tagme, open('/home/vprovat/EL_pickles/entries_top_tagme.p', 'wb'))