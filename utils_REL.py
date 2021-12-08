from REL.mention_detection import MentionDetection
from REL.ner import load_flair_ner
from REL.utils import process_results
from REL.entity_disambiguation import EntityDisambiguation
wiki_version = "wiki_2019"
base_url = '/ivi/ilps/personal/vprovat/REL_files'

def convert_input(entry):
    '''
    In: a ShadowLink entry
    Out: the same entry but in REL's input format
    '''
    text_raw = entry['example']
    # correct = entry['correct_entity_name']
    span = entry['span']

    return {"doc_1": [text_raw, [span]]}  # we don't want REL to think documents are connected


def preprocess(text):
    processed = {"test_doc1": [text, []]}
    return processed


def spans_to_REL(entry):
    spans = [entry['span']] + [[x[0], x[1]] for x in entry['context_entities']]
    processed = {"doc_1": [entry['example'], spans]}
    return processed

mention_detection = MentionDetection(base_url, wiki_version)
def get_mentions_dataset(entry_REL, max_num_candidates=30):
    '''
    In: a REL-friendly entry {'doc_1': ["Text",
                                         [(mention_begins, mention_ends)]
                                       ]
                            },
        target mention (eg. Grayling)

    Out: "mentions dataset" with candidates selected by REL
    '''
    mentions_dataset, n_mentions = mention_detection.format_spans(entry_REL)

    for mention in mentions_dataset['doc_1']:
        mention['candidates'] = mention['candidates'][:max_num_candidates]

    return mentions_dataset