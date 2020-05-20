import numpy as np
import pandas as pd
import nltk
import nltk.data
import re
from nltk.corpus import stopwords
import string
from nltk.stem.snowball import SnowballStemmer

class FeatureTokenizer:

    def __init__(self):
        self.stopwords_set = set(stopwords.words('english'))
        self.number_regexp_pattern = re.compile(r'.*[\d].*')

    def remove_stopwords(self, words):
        return [w for w in words if w not in self.stopwords_set and self.number_regexp_pattern.search(w) is None]

    def remove_urls(self, s, replace=''):
        return re.sub(r'(https?://\S+)', replace, s)

    def stem_words(self, words, stemmer = SnowballStemmer("english")):
        return {stemmer.stem(word) for word in words}

    def punct_filter(self, s):
        translator = str.maketrans('', '', string.punctuation + '')
        return s.translate(translator)

    def words_tokenize(self, text, sents_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle'), words_tokenizer = nltk.wordpunct_tokenize):
        sents = sents_tokenizer.tokenize(text.strip())
        words = [words_tokenizer(sentence) for sentence in sents]
        tokens = set()
        tokens.update({self.punct_filter(w) for word in words for w in word})
        return tokens

    def tokenize(self, text):
        urls_removed = self.remove_urls(text)
        word_tokens = self.words_tokenize(urls_removed)
        stemmed = self.stem_words(word_tokens)
        return self.remove_stopwords(stemmed)

if __name__ == '__main__':
    print("main function")
    data = pd.read_csv('./incident.csv',  encoding = "ISO-8859-1")
    print("\n=======================Data Info =========================================\n")
    print(data.info())
    print("\n==========================================================================\n")
    row_number = np.random.randint(data.shape[0])
    text = data.loc[row_number, 'description']
    print("Original Text: \n")
    tokenizer = FeatureTokenizer()
    print("\nTokenized features:\n")
    print(tokenizer.tokenize(text))

