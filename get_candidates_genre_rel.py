from REL.mention_detection import MentionDetection
from REL.ner import load_flair_ner
from REL.utils import process_results
from REL.entity_disambiguation import EntityDisambiguation

wiki_version = "wiki_2019"
base_url = '/ivi/ilps/personal/vprovat/REL_files'


from utils_REL import *

import json
from collections import namedtuple

MentionEntry = namedtuple('MentionEntry', 'mention candidates')
CandidateEntry = namedtuple("CandidateEntry", 'candidate score')


def process_candidates(mentions_dataset, threshold=0):
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


from tqdm.auto import tqdm
import pickle

mention_detection = MentionDetection(base_url, wiki_version)


def get_candidates_end2end():
    tagger_ner = load_flair_ner("ner-fast")
    top = json.load(open('ShadowLink/Top.json', 'r'))

    entries_top = []
    for entry in top:
        gt_mention = entry['entity_space_name'].lower()
        example = entry['example']
        input_text = preprocess(example)
        mentions_dataset, n_mentions = mention_detection.find_mentions(input_text, tagger_ner)
        mentions_found = [item['mention'].lower() for item in mentions_dataset['test_doc1']]
        if not gt_mention in mentions_found:
            print('target entity not found:')
            print(gt_mention)
            print(example)
            print(mentions_found)
            print()
            continue

        cands_dataset = process_candidates(mentions_dataset['test_doc1'])
        if len(cands_dataset) > 1:
            entries_top.append(cands_dataset)

    pickle.dump(entries_top, open('pickles/entries_top.p', 'wb'))

from tqdm.auto import tqdm
if __name__ == '__main__':
    shadow_w_context = pickle.load(open('pickles/shadow_w_context_latest.p', 'rb'))
    top_w_context = pickle.load(open('/home/vprovat/GENRE_experiments/pickles/top_w_context_latest.p', 'rb'))
    print(len(top_w_context))

    entries_top_genre = []  # ner by genre, candidate retrieval by rel
    for item in tqdm(top_w_context):
        entry = spans_to_REL(item)
        dataset = get_mentions_dataset(entry)
        cands_dataset = process_candidates(dataset['doc_1'])
        entries_top_genre.append(cands_dataset)

    pickle.dump(entries_top_genre, open('pickles/entries_top_genre.p', 'wb'))

    # entries_shadow_genre = []  # ner by genre, candidate retrieval by rel
    # for item in tqdm(shadow_w_context):
    #     entry = spans_to_REL(item)
    #     dataset = get_mentions_dataset(entry)
    #     cands_dataset = process_candidates(dataset['doc_1'])
    #     entries_shadow_genre.append(cands_dataset)
    #
    # pickle.dump(entries_shadow_genre, open('pickles/entries_shadow_genre.p', 'wb'))
