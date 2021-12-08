from collections import namedtuple

MentionEntry = namedtuple('MentionEntry', 'mention candidates')
CandidateEntry = namedtuple("CandidateEntry", 'candidate score')
EvalResult = namedtuple("EvalResult", "mw jaccard lm w2v conditionalprobability pmi barabasialbert")
import pickle


def p_r_f(res):
    P = res['tp'] / (res['tp'] + res['fp'])
    R = res['tp'] / (res['tp'] + res['fn'])
    F = 2 * P * R / (P + R)
    return P, R, F

def correct_answer(ans, correct):
    return ans.replace('_', ' ') == correct

def evaluate(gt, preds):
    res = {'tp': 0, 'fp': 0, 'tn': 0, 'fn': 0, 'acc': 0, 'nil': 0}
    for gt_item, pred_item in zip(gt, preds):
        print(gt_item)
        print(pred_item)
        target_mention = gt_item['entity_space_name']
        is_NIL = True
        # if len(pred_item) < 2: # excluding entities without enough context
        #     continue
        for mention in pred_item:
            if mention.mention.lower() == target_mention.lower():
                is_NIL = False
                ans = mention.candidates # actually one candidate
                correct = gt_item['entity_name']
                if correct_answer(ans, correct):
                    res['tp'] += 1
                else:
                    # print(ans, correct)
                    res['fp'] += 1
                    res['fn'] += 1
        if is_NIL:
            res['nil'] += 1
            print(target_mention, pred_item)
            # print('FUCK')
            # print(gt_item)
            # print(pred_item)
            # print()
    res['acc'] = res['tp'] / (res['tp'] + res['fp'])
    return res

def find_gt(sampled, gt):  # because I forgot to save GT for a sample separately
    res = []
    for entry in sampled:
        first_mention = entry[0].mention
        last_mention = entry[-1].mention
        found = False
        for gt_entry in gt:
            where_to_find = gt_entry['example'].lower().replace(' ', '').replace('\'', '')
            if where_to_find.find(first_mention.lower().replace(' ', '').replace('\'', '')) != -1:
                if where_to_find.find(last_mention.lower().replace(' ', '').replace('\'', '')) != -1:
                    res.append(gt_entry)
                    found = True
                    # print(first_mention, last_mention)
                    # print(gt_entry['example'])
                    # print(gt_entry['entity_space_name'])
                    break
                # else:
                #     print(last_mention, gt_entry['example'])

        if not found:
            print('FUCK')
            print(first_mention, last_mention)
    return res

import json
if __name__ == '__main__':
    path_to_data = '/home/vprovat/EL_dataset/ShadowLink'
    shadow = json.load(open(path_to_data + '/Shadow.json', 'r'))
    top = json.load(open(path_to_data + '/Top.json', 'r'))

    # top_sampled = pickle.load(open('/home/vprovat/EL_pickles/entries_top_tagme_sample_200.p', 'rb')) # first setup
    # PATH_TO_ANSWERS = '/home/vprovat/EL_pickles/res_top_tagme_sample_200_{0}_{1}.p'

    # top_sampled = pickle.load(open('/home/vprovat/EL_pickles/entries_top_REL.p', 'rb')) # second setup
    # PATH_TO_ANSWERS = '/home/vprovat/EL_pickles/res_top_REL_NER_all_{0}_{1}.p'

    # top_sampled = pickle.load(open('/home/vprovat/EL_pickles/entries_top_REL_ner_no_threshold.p', 'rb')) # third setup
    # PATH_TO_ANSWERS = '/home/vprovat/EL_pickles/res_top_REL_NER_all_no_threshold_{0}_{1}.p'


    PATH_TO_ENTRIES = '/home/vprovat/EL_pickles/entries_shadow_REL_ner_with_threshold.p'
    data_sampled = pickle.load(open(PATH_TO_ENTRIES, 'rb'))  # 4th setup
    # PATH_TO_ANSWERS = '/home/vprovat/EL_pickles/res_shadow_REL_NER_all_with_threshold_{0}_{1}.p' # shadow
    # PATH_TO_ANSWERS = '/home/vprovat/EL_pickles/res_shadow_AIDA_v0.p'
    PATH_TO_ANSWERS = '/home/vprovat/EL_pickles/res_shadow_REL_NER_all_with_threshold_{0}_{1}_priordiff_randomfirst.p'
    # PATH_TO_ANSWERS = '/home/vprovat/EL_pickles/res_shadow_REL_NER_all_with_threshold_{0}_{1}_numcands_randomfirst.p'
    gt = find_gt(data_sampled, shadow) # NB: change to Top when needed
    print(len(gt))

    # relatedness = ['mw', 'jaccard', 'lm', 'w2v', 'conditionalprobability', 'pmi', 'barabasialbert']
    relatedness = ['mw', 'pmi']
    aggr = ['avg', 'min']
    eval_res = {'avg': [], 'min': []}
    for measure in relatedness:
        for agg in aggr:
            print(measure, agg)
            try:
                # pred = pickle.load(open('/home/vprovat/EL_pickles/res_top_tagme_sample_200_{0}_{1}.p'.format(measure, agg), 'rb'))
                pred = pickle.load(open(PATH_TO_ANSWERS.format(measure, agg), 'rb'))
            except:
                continue
            # print(gt)
            # print(pred)
            res = evaluate(gt, pred)
            print(res)
            print(p_r_f(res))
            print()
            eval_res[agg].append(res['acc'])
            # print(relatedness, aggr, res)

    print('      ' + '    '.join(relatedness))
    print('avg', list(format(x, '.3f') for x in eval_res['avg']))
    print('min', list(format(x, '.3f') for x in eval_res['min']))
    # print("avg: ", EvalResult(x for x in eval_res['avg']))
    # print("min: ", EvalResult(x for x in eval_res['min']))