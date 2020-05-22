def define_class(text):
    import pickle
    import re
    import nltk

    nltk.download('stopwords')
    from nltk.corpus import stopwords
    from pymystem3 import Mystem

    russian_stopwords = stopwords.words("russian")
    mystem = Mystem()

    E_RE = re.compile(r'ё')
    PUNCTUATION_RE = re.compile(r'[!"#$%&\'()*+,./:;<=>?@[\\]^_`{|}~]')
    GOOD_SYMBOLS_RE = re.compile(r'[^a-za-я\- ]')
    DUPLICATE_SPACES_RE = re.compile(r'\s+')

    def prepare_text(text):
        text = text.lower()

        text = E_RE.sub('е', text)
        text = PUNCTUATION_RE.sub(' ', text)
        text = GOOD_SYMBOLS_RE.sub('', text)

        text = ' '.join(mystem.lemmatize(text))

        text = ' '.join([token for token in text.split(' ') if token not in russian_stopwords])

        text = DUPLICATE_SPACES_RE.sub(' ', text).strip(' ')
        return text

    def load_model(path):
        with open(path, 'rb') as f:
            return pickle.load(f)

    clf = load_model('models/classifier_lb.pkl')
    lb = load_model('models/label.pkl')
    vectorizer = load_model('models/vectorizer_lb.pkl')

    vect = vectorizer.transform([prepare_text(text)])
    pred = lb.inverse_transform(clf.predict(vect))

    if vect.count_nonzero() == 0 or len(pred) == 0:
        return 'Другое'
    else:
        return pred[0]