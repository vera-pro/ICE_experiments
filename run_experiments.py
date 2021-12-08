from collections import namedtuple
MentionEntry = namedtuple('MentionEntry', 'mention candidates')
CandidateEntry = namedtuple("CandidateEntry", 'candidate score')

from tqdm.auto import tqdm
import pickle
from utils import *
import numpy as np


def find_relatedness(new_entity_id, existing_entity_ids, measure='barabasialbert', aggregate='avg'):
    """
    :param new_entity_id: Wikipedia ID of the new entity candidate
    :param existing_entity_ids: Wikipedia ID's of the candidates already added to the set
    :param measure:  measure used to calculate relatedness with WAT API.
        options: ''mw', 'jaccard', 'lm', 'w2v', 'conditionalprobability', 'pmi', 'barabasialbert'
    :param aggregate: method for relatedness aggregation.
        options: 'avg', 'min'

    :return: aggregated relatedness between the new entity candidate and the existing ones
    """
    scores = [wat_relatedness_pairwise(new_entity_id, ent_id, measure) for ent_id in existing_entity_ids]
    if aggregate == 'avg':
        return np.mean(scores)
    if aggregate == 'min':
        return np.min(scores)

import random
random.seed(42)
def pick_random_candidate(mention):
    # Pick a random candidate: probabilities are proportional to priors
    choose_from = []
    for cand in mention.candidates:
        choose_from.extend([cand]*int(100*cand.score))
    return random.choice(choose_from)

def pick_random_mention(mentions_list):
    # Pick a random candidate: probabilities are proportional to priors
    choose_from = []
    for ment in mentions_list:
        choose_from.extend([ment]*int(100-len(ment.candidates)))
    return random.choice(choose_from)

def disambiguate(mentions, measure='barabasialbert', aggregate='avg'):
    """
    :param mentions: list of all mentions and their candidates
    :param measure: measure used to calculate relatedness with WAT API
        options: ''mw', 'jaccard', 'lm', 'w2v', 'conditionalprobability', 'pmi', 'barabasialbert'
    :param aggregate: method for relatedness aggregation
        options: 'avg', 'min'

    :return: disambiguation result: one candidate per entity
    """

    sorted_mentions = sorted(mentions, key=lambda x: -len(x.candidates))
    # todo: add processing for NILs!
    # sorted_mentions = sorted(mentions, key=lambda x: x.candidates[1].score - x.candidates[0].score if len(x.candidates) > 1 else -x.candidates[0].score)

    first_mention = sorted_mentions.pop()  # Least ambiguous
    res = []
    while sorted_mentions and not first_mention.candidates:  # processing NILs first
        res.append(MentionEntry(first_mention.mention, 'NIL'))
        first_mention = sorted_mentions.pop()

    first_cand = pick_random_candidate(first_mention).candidate # chosen randomly, probabilities proportional to priors
    cur_cands = [first_cand]
    res.append(MentionEntry(first_mention.mention, first_cand))
    cur_ids = [wat_wiki_id(first_cand)]  # to minimize the number of WAT queries

    while sorted_mentions:
        cur_mention = sorted_mentions.pop()
        cur_relatedness = -1
        cur_best_cand = None
        cur_best_id = None

        for cand in cur_mention.candidates:
            cand_id = wat_wiki_id(cand.candidate)
            if cand_id in cur_ids:  # duplicate mention extracted, a bug in get_candidates_with_rel
                continue
            if None in cur_ids:
                print('WTF')
                print(mentions)
                print(cur_ids)
            relatedness_score = find_relatedness(cand_id, cur_ids, measure, aggregate)
            if relatedness_score > cur_relatedness:
                cur_relatedness = relatedness_score
                cur_best_cand = cand.candidate
                cur_best_id = cand_id

        if not cur_best_cand:
            continue  # duplicate mention

        cur_cands.append(cur_best_cand)
        cur_ids.append(cur_best_id)
        res.append(MentionEntry(cur_mention.mention, cur_best_cand))

    return res


if __name__ == '__main__':
    # entries_shadow = pickle.load(open('/home/vprovat/EL_pickles/entries_shadow_tagme_sample_200.p', 'rb'))
    # entries_top = pickle.load(open('/home/vprovat/EL_pickles/entries_top_tagme_sample_200.p', 'rb'))

    # entries_top = pickle.load(open('/home/vprovat/EL_pickles/entries_top_REL.p', 'rb'))

    # PATH_TO_ENTRIES = '/home/vprovat/EL_pickles/entries_top_REL_ner_no_threshold.p'
    PATH_TO_ENTRIES = '/home/vprovat/EL_pickles/entries_shadow_REL_ner_with_threshold.p'
    entries = pickle.load(open(PATH_TO_ENTRIES, 'rb'))

    # PATH_TO_ANSWERS = '/home/vprovat/EL_pickles/res_shadow_REL_NER_all_with_threshold_{0}_{1}_priordiff_randomfirst.p'
    PATH_TO_ANSWERS = '/home/vprovat/EL_pickles/res_shadow_REL_NER_all_with_threshold_{0}_{1}_numcands_randomfirst.p'

    # relatedness = ['mw', 'jaccard', 'lm', 'w2v', 'conditionalprobability', 'pmi', 'barabasialbert']
    relatedness = ['pmi']  #['mw', 'pmi'] # best so far
    aggr = ['avg'] #, 'min'] # stopped using min because it seems to be worse for all measures except w2v
    print('hi\n')
    for measure in relatedness:
        for agg in aggr:
            print(measure, agg)
            try:
                res = pickle.load(open(PATH_TO_ANSWERS.format(measure, agg), 'rb'))
            except:
                res = []

            cnt = 0
            cur_len = len(res)
            print(cur_len)
            for entry in tqdm(entries[cur_len:]):
                if cnt and cnt % 10 == 0:
                    print(res[-1])
                    pickle.dump(res, open(PATH_TO_ANSWERS.format(measure, agg), 'wb'))
                cnt += 1
                res.append(disambiguate(entry, measure, agg))
            print('Finished step')
            print(res[:5])
            pickle.dump(res, open(PATH_TO_ANSWERS.format(measure, agg), 'wb'))
