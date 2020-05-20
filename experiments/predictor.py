from joblib import load

class TfidfRandomForestPredictor():
    def __init__(self, model_file, vectorizer_file):
        self.tfidf = load(vectorizer_file)
        self.classifier = load(model_file)

    def predict(self, text):
        input_matrix = self.tfidf.transform([content])
        return self.classifier.predict(input_matrix)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-m", "--model-file", help="where to load model file", metavar="FILE")
    parser.add_argument("-i", "--input-text-file", help="input free text filename")
    parser.add_argument("-v", "--vectorizer-file", help="vectorizer for extracting features and vectorize them")
    args = parser.parse_args()
    with open(args.input_text_file, 'r') as content_file:
        content = content_file.read()
    predictor = TfidfRandomForestPredictor(args.model_file, args.vectorizer_file)
    result = predictor.predict(content)
    print("The predicted result is: ", result)
