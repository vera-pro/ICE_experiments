from REL.db.generic import GenericLookup
from REL.utils import preprocess_mention
from REL.mention_detection import MentionDetection
from ner_tagger import *
from REL.ner import NERBase, Span

base_url = '/ivi/ilps/personal/vprovat/REL_files'
wiki_version = "wiki_2019"

class CandidatesGetter:
    def __init__(self):
        self.tagger = MD_Module()
        self.REL = MentionDetection(base_url, wiki_version)

    def process_sentence(self, sentence):
        mentions = self.tagger.find_mentions(sentence)
        dataset = {'doc1': [sentence, [(span.start_pos, span.end_pos-span.start_pos+1) for span in mentions]]}
        res = self.REL.format_spans(dataset)
        return res

if __name__ == "__main__":
    getter = CandidatesGetter()
    getter.process_sentence("Like Michael Jordan, Jens Lehmann is also a scientist. One went to Rome, the other prefers Odessa")