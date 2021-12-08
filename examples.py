from REL.mention_detection import MentionDetection
from REL.utils import process_results
from REL.entity_disambiguation import EntityDisambiguation
from REL.ner import Cmns, load_flair_ner

wiki_version = "wiki_2019"
base_url = '/ivi/ilps/personal/vprovat/REL_files'

def example_preprocessing():
    # user does some stuff, which results in the format below.
    text = "Obama will visit Germany. And have a meeting with Merkel tomorrow."
    processed = {"test_doc1": [text, []], "test_doc2": [text, []]}
    return processed

def example_end2end():
    mention_detection = MentionDetection(base_url, wiki_version)
    tagger_ner = load_flair_ner("ner-fast")
    input_text = example_preprocessing()
    mentions_dataset, n_mentions = mention_detection.find_mentions(input_text, tagger_ner)

    config = {
        "mode": "eval",
        "model_path": base_url + "/ed-wiki-2019/model",
    }

    model = EntityDisambiguation(base_url, wiki_version, config)
    predictions, timing = model.predict(mentions_dataset)

    result = process_results(mentions_dataset, predictions, input_text)
    print(result)