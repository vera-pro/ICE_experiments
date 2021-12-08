from nltk.tag import StanfordNERTagger
from nltk.tokenize import word_tokenize

def test_tagger():
    st = StanfordNERTagger('/usr/share/stanford-ner/classifiers/english.all.4class.distsim.crf.ser.gz',
                           '/usr/share/stanford-ner/stanford-ner.jar',
                           encoding='utf-8')

    text = 'While in France, Christine Lagarde discussed short-term stimulus efforts in a recent interview with the Wall Street Journal.'

    tokenized_text = word_tokenize(text)
    classified_text = st.tag(tokenized_text)

    print(classified_text)

if __name__  == '__main__':
    test_tagger()