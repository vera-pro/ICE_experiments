from collections import namedtuple
from typing import List
import re

from nltk.tag import StanfordNERTagger
from nltk.tokenize import word_tokenize

PATH_TO_STANFORD_classifier = '/ivi/ilps/personal/vprovat/stanford-ner-2020-11-17/classifiers/english.conll.4class.distsim.crf.ser.gz'
PATH_TO_STANFORD_jar = '/ivi/ilps/personal/vprovat/stanford-ner-2020-11-17/stanford-ner.jar'

from REL.ner import NERBase, Span
# Span is defined as:
#   namedtuple("Span", ["text", "start_pos", "end_pos", "score", "tag"])

from REL.mention_detection_base import MentionDetectionBase
from abc import ABC, abstractmethod
from collections import namedtuple


# Span = namedtuple("Span", ["text", "start_pos", "end_pos", "score", "tag"])

class MD_Module(NERBase, MentionDetectionBase):
    def __init__(self,
                 path_to_classifier='/ivi/ilps/personal/vprovat/stanford-ner-2020-11-17/classifiers/english.conll'
                                    '.4class.distsim.crf.ser.gz',
                 path_to_jar='/ivi/ilps/personal/vprovat/stanford-ner-2020-11-17/stanford-ner.jar'):
        self.st = StanfordNERTagger(path_to_classifier,
                                    path_to_jar,
                                    encoding='utf-8')

    def predict(self, sentence, sentences_doc) -> List[Span]:
        """
        This function is mandatory and overrides NERBase.predict(self, *args, **kwargs).

        The module takes as input: a sentence from the current doc and all the sentences of
        the current doc (for global context). The user is expected to return a list of mentions,
        where each mention is a Span class.

        We denote the following requirements:
        1. Any MD module should have a 'predict()' function that returns a list of mentions.
        2. A mention is always defined as a Span class (see above).

        """
        # returns list of Span objects
        return self.find_mentions(sentence)

    def find_mentions(self, sentence):
        '''
        NB: won't work if you have multiple whitespaces clumped together!
        :param sentence:
        :return:
        '''
        mentions = []
        tokenized_text = word_tokenize(sentence)
        classified_text = self.st.tag(tokenized_text)

        spaces = [(m.start(0), m.end(0)) for m in re.finditer('[\s]{1,}', sentence)] # to deal with multiple whitespaces
        cur_space_ind = 0

        cur_ment = None
        cur_start = -1
        cur_tag = None
        cur_total_length = 0

        for item in classified_text:
            if cur_space_ind < len(spaces) and cur_total_length >= spaces[cur_space_ind][0]:
                cur_total_length += spaces[cur_space_ind][1] - spaces[cur_space_ind][0]
                cur_space_ind += 1
            if item[-1] == 'O':  # mention either ended or not started
                if cur_ment:
                    mentions.append(Span(cur_ment, cur_start, cur_start + len(cur_ment) - 1, 1, cur_tag))
                    if sentence.find(cur_ment) != cur_start:
                        print('WTF? Mention [{0}] expected at {1} but found at {2}'.format(cur_ment, sentence.find(cur_ment),
                                                                                         cur_start))
                cur_ment = None
                cur_start = -1
                cur_tag = None
            else:  # mention either continues or begins
                if cur_ment:
                    if item[-1] == cur_tag:  # still the same mention, new word
                        cur_ment += ' ' + item[0]
                    else:  # a new mention with a different class
                        mentions.append(Span(cur_ment, cur_start, cur_start + len(cur_ment) - 1, 1, cur_tag))
                        if sentence.find(cur_ment) != cur_start:
                            print('WTF? Mention [{0}] expected at {1} but found at {2}'.format(cur_ment,
                                                                                             sentence.find(cur_ment),
                                                                                             cur_start))
                        cur_ment = item[0]
                        cur_start = cur_total_length
                        cur_tag = item[-1]
                else:  # a new mention begins
                    cur_ment = item[0]
                    cur_start = cur_total_length
                    cur_tag = item[-1]
            cur_total_length += len(item[0])

        if cur_ment:  # last mention
            mentions.append(Span(cur_ment, cur_start, cur_start + len(cur_ment) - 1, 1, cur_tag))
            if sentence.find(cur_ment) != cur_start:
                print('WTF? Mention {0} expected at {1} but found at {2}'.format(cur_ment, sentence.find(cur_ment),
                                                                                 cur_start))

        return mentions

    def get_spans(self, sentence):
        ments = self.find_mentions(sentence)
        res = {'doc': [sentence]}


if __name__ == '__main__':
    tagger = MD_Module(PATH_TO_STANFORD_classifier, PATH_TO_STANFORD_jar)
    mentions = tagger.find_mentions(" Bertje,   Michael Jordan,\t Jens Lehmann     and your mom visited Odessa yesterday. Cheers from Amsterdam")
    print(mentions)
