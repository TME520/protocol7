from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import pandas as pd

class TfidfFeatureExtractor:
    def __init__(self, tokenizer, batch_size = 200, max_features = 1000):
        self.batch_size = batch_size
        self.max_features = max_features
        self.tokenizer = tokenizer
        self.tfidf = TfidfVectorizer(tokenizer=self.tokenizer, stop_words='english', max_features=self.max_features)

    def extract(self, texts):
        return self.tfidf.fit_transform(texts)

def create_target_column(data):
    data.loc[data['u_solution'] == 'Incorrectly Assigned', 'target'] = 0
    data.loc[data['u_solution'] != 'Incorrectly Assigned', 'target'] = 1
    return data

def training_testing_split(data):
    positive_target_indices = data[data['target'] == 1].index
    negative_target_indices = data[data['target'] == 0].index
    pos_train_indices = np.random.choice(positive_target_indices, round(0.8*positive_target_indices.shape[0]), replace=False)
    neg_train_indices = np.random.choice(negative_target_indices, round(0.8*negative_target_indices.shape[0]), replace=False)
    train_indices = np.hstack((pos_train_indices, neg_train_indices))
    test_indices = np.array(list(set(data.index.values) - set(train_indices)))
    return (train_indices, test_indices)


if __name__ == "__main__":
    import texts_nlp_process as tnp
    print("main function")
    data = pd.read_csv('./incident.csv',  encoding = "ISO-8859-1")
    print("\n======================= Data Info =========================================\n")
    print(data.info())
    print("\n==========================================================================\n")
    tokenizer = tnp.FeatureTokenizer()
    extractor = TfidfFeatureExtractor(tokenizer.tokenize)
    sparse_tfidf_texts = extractor.extract(data['description'].tolist())
    data = create_target_column(data)
    (train_indices, test_indices) = training_testing_split(data)
    print("\n======================= Training and Testing Data Shape =========================================\n")
    print("Training Data: ", train_indices.shape, "\n")
    print("Testing Data: ", test_indices.shape, "\n")
    from joblib import dump, load
    dump(extractor.tfidf, './models/tfidf_vectorizer_0403-TME520.joblib')
    
