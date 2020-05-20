import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import os

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

stopWords = set(stopwords.words('english'))
crapWords = [';', ':', '-', '.', ',', '(', ')', '[', ']', '&', '--', '#']
wordnet_lemmatizer = WordNetLemmatizer()

print("Lemmatization test with churches: " + wordnet_lemmatizer.lemmatize('updated'))

cb1DataFolder = os.environ.get('CB1DATAFOLDER')
print("CB1 data folder: " + cb1DataFolder)
cb1Files = [f.name for f in os.scandir(cb1DataFolder) if f.is_file() and f.name.endswith('.cb1')]
print(cb1Files)
for f in cb1Files:
    print("\n------ " + f + " ------")
    currentCB1File = open(cb1DataFolder + f, 'r')
    currentDescription = currentCB1File.readlines()
    currentCB1File.close()
    for g in currentDescription:
        currentCB1File = open(cb1DataFolder + f + '.processed', 'w')
        currentCB1File.write("--- FILTERED DATA ---\n")
        # Remove empty lines + crap characters
        if g != '' and g!='\n':
            tokens = nltk.word_tokenize(g)
            wordsFiltered = []
            
            for w in tokens:
                if (w.lower() not in stopWords) and (w.lower() not in crapWords):
                    word_lemme = wordnet_lemmatizer.lemmatize(w.lower())
                    wordsFiltered.append(word_lemme)
            currentCB1File.write(str(wordsFiltered))
            currentCB1File.write("\n--- *** ---")
            currentCB1File.close()
            print(str(wordsFiltered))