from REL.mention_detection import MentionDetection
from REL.utils import process_results
from REL.entity_disambiguation import EntityDisambiguation
# from REL.ner import Cmns, load_flair_ner
from ner_tagger import *
import json
from utils_REL import *

base_url = '/ivi/ilps/personal/vprovat/REL_files'
wiki_version = "wiki_2019"

def example_preprocessing():
    # user does some stuff, which results in the format below.
    text = "Obama will visit Germany. And have a meeting with Merkel tomorrow."
    processed = {"test_doc1": [text, []], "test_doc2": [text, []]}
    return processed

from collections import namedtuple
MentionEntry = namedtuple('MentionEntry', 'mention candidates')
CandidateEntry = namedtuple("CandidateEntry", 'candidate score')

def process_candidates(mentions_dataset, threshold=0.01):
    res = []
    mentions_used = set()
    for item in mentions_dataset:
        if item['mention'] in mentions_used: # preventing duplicates
            continue
        mentions_used.add(item['mention'])
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
from tqdm.auto import tqdm

def get_candidates_end2end(tagger, in_path='ShadowLink/Top.json',
                           out_path='/home/vprovat/EL_pickles/entries_top_REL.p'):
    data = json.load(open(in_path, 'r'))

    res = []
    for entry in tqdm(data):
        gt_mention = entry['entity_space_name'].lower()
        example = entry['example']
        input_text = preprocess(example)
        mentions_dataset, n_mentions = mention_detection.find_mentions(input_text, tagger) # which format does it expect from tagger?
        mentions_found = [item['mention'].lower() for item in mentions_dataset['test_doc1']]
        if not gt_mention in mentions_found:
            print('target entity not found:')
            print(gt_mention)
            print(example)
            print(mentions_found)
            print()
            spans = [[example.lower().find(entry['entity_space_name'].lower()),
                          len(entry['entity_space_name'])]
                         ]
            extra_entry = {"doc_1": [example, spans]}
            extra_data = get_mentions_dataset(extra_entry)
            mentions_dataset['test_doc1'] += extra_data['doc_1']
            print(mentions_dataset)

        cands_dataset = process_candidates(mentions_dataset['test_doc1'])
        if len(cands_dataset) > 1:
            res.append(cands_dataset)

    print(len(res), " entries processed")
    pickle.dump(res, open(out_path, 'wb'))


if __name__ == '__main__':
    # input_text = example_preprocessing()
    mention_detection = MentionDetection(base_url, wiki_version)
    # tagger_ner = load_flair_ner("ner-fast")
    # tagger_ngram = Cmns(base_url, wiki_version, n=5)
    tagger_st = MD_Module()

    sample = {"test_doc": ["the brown fox jumped over the lazy dog", [[10, 3], [35,3]]]}
    mentions_dataset, total_mentions = mention_detection.format_spans(sample)
    print(mentions_dataset)
    exit(0)

    get_candidates_end2end(tagger_st, in_path='ShadowLink/Top.json',
                           out_path='/home/vprovat/EL_pickles/entries_top_REL_stanford_with_threshold.p')
    get_candidates_end2end(tagger_st, in_path='ShadowLink/Shadow.json',
                           out_path='/home/vprovat/EL_pickles/entries_shadow_REL_stanford_with_threshold.p')

    # get_candidates_end2end(tagger_ngram, in_path='ShadowLink/Top.json',
    #                        out_path='/home/vprovat/EL_pickles/entries_top_REL_ngram_no_threshold.p')
    # get_candidates_end2end(tagger_ngram, in_path='ShadowLink/Shadow.json',
    #                        out_path='/home/vprovat/EL_pickles/entries_shadow_REL_ngram_no_threshold.p')

    # for n_val in (5, 6):  # UPD: just use 5, it detects n-grams of smaller length too
    #     tagger_ngram = Cmns(base_url, wiki_version, n=n_val)
    #     get_candidates_end2end(tagger_ner, in_path='ShadowLink/Shadow.json',
    #                        out_path='/home/vprovat/EL_pickles/entries_shadow_REL_ngram_{0}.p'.format(n_val))
    #     get_candidates_end2end(tagger_ner, in_path='ShadowLink/Top.json',
    #                        out_path='/home/vprovat/EL_pickles/entries_top_REL_ngram_{0}.p'.format(n_val))