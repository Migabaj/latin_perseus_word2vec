import logging
import os
import sys
import time
import regex
import json

from cltk.utils.cltk_logger import logger

# TODO: Fix this
# KJ added this to fix failing build on Travis CI. Gensim seems to load boto, which in turn causes an error.
try:
    from gensim.models import Word2Vec
except AttributeError:
    logger.error('Command `from gensim.models import Word2Vec` failed with AttributeError.')


from cltk.corpus.utils.formatter import phi5_plaintext_cleanup
from cltk.corpus.utils.formatter import tlg_plaintext_cleanup
from cltk.corpus.utils.formatter import assemble_phi5_author_filepaths
from cltk.corpus.utils.formatter import assemble_tlg_author_filepaths
from cltk.stem.latin.j_v import JVReplacer
from cltk.stem.lemma import LemmaReplacer
from cltk.stop.latin import STOPS_LIST as latin_stops
from cltk.tokenize.sentence import TokenizeSentence
from cltk.tokenize.word import WordTokenizer
from cltk.corpus.latin.perseus_corpus_types import perseus_corpus_texts_by_type

def general_cleanup(text, rm_punctuation=False, rm_periods=False):
    """Remove and substitute post-processing for Greek PHI5 text.
    TODO: Surely more junk to pull out. Please submit bugs!
    TODO: This is a rather slow now, help in speeding up welcome.
    """
    # This works OK, doesn't get some
    # Note: rming all characters between {} and ()
    remove_comp = regex.compile(r'-\n|«|»|\<.+?\>|\<|\>|\.\.\.|‘|’|_|{.+?}|\(.+?\)|\(|\)|“|#|%|⚔|&|=|/|\\|〚|†|『|⚖|–|˘|⚕|☾|◌|◄|►|⌐|⌊|⌋|≈|∷|≈|∞|”|[0-9]')
    text = remove_comp.sub('', text)

    new_text = None
    if rm_punctuation:
        new_text = ''
        punctuation = [',', ';', ':', '"', "'", '?', '-', '!', '*', '[', ']', '{', '}']
        if rm_periods:
            punctuation += ['.']
        for char in text:
            # rm acute combining acute accents made by TLGU
            # Could be caught by regex, tried and failed, not sure why
            if bytes(char, 'utf-8') == b'\xcc\x81':
                pass
            # second try at rming some punctuation; merge with above regex
            elif char in punctuation:
                pass
            else:
                new_text += char
    if new_text:
        text = new_text

    # replace line breaks w/ space
    replace_comp = regex.compile(r'\n')
    text = replace_comp.sub(' ', text)

    comp_space = regex.compile(r'\s+')
    text = comp_space.sub(' ', text)

    return text

def assemble_perseus_filepaths_by_type(text_type):
    assert text_type in perseus_corpus_texts_by_type.keys()

    if not os.path.exists(get_cltk_data_dir() + f'/latin/text/{text_type}'):
        filepaths_json = [get_cltk_data_dir() + '/latin/text/latin_text_perseus/cltk_json/' + file for file in perseus_corpus_texts_by_type[text_type]]

        filepaths = []
        for file in filepaths_json:
            with open(file, encoding='utf-8') as j:
                data = json.load(j)
            data_k = data['text']
            file_text = ''
            for key in data_k.keys():
                data_k_text = data_k
                while not isinstance(data_k_text, str):
                    data_k_dict = data_k_text
                    data_k_text = data_k_text["0"]
                for value in data_k_dict.values():
                    file_text += value+'\n'
            new_txt_file = f'{text_type}/{os.path.splitext(os.path.split(file)[1])[0]}.txt'
            if not os.path.exists(os.path.split(new_txt_file)[0]):
                os.mkdir(os.path.split(new_txt_file)[0])
            with open(new_txt_file, 'w', encoding='utf-8') as plain:
                plain.write(file_text)
            filepaths.append(new_txt_file)

    else:
        print('ok')
        filepaths = []
        for file in os.listdir(get_cltk_data_dir() + f'/latin/text/{text_type}/'):
            filepath = get_cltk_data_dir() + f'/latin/text/{text_type}/{file}'
            filepaths.append(filepath)

    return filepaths


def assemble_perseus_author_filepaths():
    """Builds a list of absolute filepaths for Perseus."""
    authors_dir_rel = get_cltk_data_dir() + '/latin/text/latin_text_perseus/'
    authors_dir = os.path.expanduser(authors_dir_rel)
    filepaths = []
    for potential_author in os.listdir(authors_dir):
        pot_author_path = authors_dir+potential_author
        if os.path.isdir(pot_author_path):
            if os.path.exists(pot_author_path+'/opensource'):
                for file in os.listdir(pot_author_path+'/opensource/'):
                    if os.path.splitext(file)[1] == '.xml':
                        if os.path.splitext(file)[0].endswith('_lat'):
                            filepaths.append(pot_author_path+'/opensource/'+file)
    return filepaths

def assemble_ignis_poetry_filepaths():
    poetry_dir_rel = get_cltk_data_dir() + '/latin/text/latin_text_ignis/poetry/'
    poetry_dir = os.path.expanduser(poetry_dir_rel)
    filepaths = []
    for filename in os.listdir(poetry_dir):
        filepath = poetry_dir + filename
        filepaths.append(filepath)
    return filepaths

def assemble_ignis_prose_filepaths():
    poetry_dir_rel = get_cltk_data_dir() + '/latin/text/latin_text_ignis/prose/'
    poetry_dir = os.path.expanduser(poetry_dir_rel)
    filepaths = []
    for filename in os.listdir(poetry_dir):
        filepath = poetry_dir + filename
        filepaths.append(filepath)
    return filepaths

def gen_docs(corpus, lemmatize, rm_stops):
    """Open and process files from a corpus. Return a list of sentences for an author. Each sentence
    is itself a list of tokenized words.
    """

    assert corpus in [
        'phi5',
        'tlg',
        'latin_text_perseus',
        'latin_text_ignis_poetry',
        'latin_text_ignis_prose',
        'perseus.early_silver',
        'perseus.late_silver',
        'perseus.christian',
        'perseus.augustan',
        'perseus.old',
        'perseus.republican'
    ]

    if corpus == 'phi5':
        language = 'latin'
        filepaths = assemble_phi5_author_filepaths()
        jv_replacer = JVReplacer()
        text_cleaner = phi5_plaintext_cleanup
        word_tokenizer = WordTokenizer('latin')
        if rm_stops:
            stops = latin_stops
        else:
            stops = None
    elif corpus == 'tlg':
        language = 'greek'
        filepaths = assemble_tlg_author_filepaths()
        text_cleaner = tlg_plaintext_cleanup
        word_tokenizer = WordTokenizer('greek')
        if rm_stops:
            stops = latin_stops
        else:
            stops = None
    elif corpus == 'latin_text_perseus':
        language = 'latin'
        filepaths = assemble_perseus_author_filepaths()
        jv_replacer = JVReplacer()
        text_cleaner = general_cleanup
        word_tokenizer = WordTokenizer('latin')
        if rm_stops:
            stops = latin_stops
        else:
            stops = None
    elif corpus == 'latin_text_ignis_poetry':
        language = 'latin'
        filepaths = assemble_ignis_poetry_filepaths()
        jv_replacer = JVReplacer()
        text_cleaner = general_cleanup
        word_tokenizer = WordTokenizer('latin')
        if rm_stops:
            stops = latin_stops
        else:
            stops = None
    elif corpus == 'latin_text_ignis_prose':
        language = 'latin'
        filepaths = assemble_ignis_prose_filepaths()
        jv_replacer = JVReplacer()
        text_cleaner = general_cleanup
        word_tokenizer = WordTokenizer('latin')
        if rm_stops:
            stops = latin_stops
        else:
            stops = None
    elif '.' in corpus and corpus.split('.')[0] == 'perseus':
        text_type = corpus.split('.')[1]
        language = 'latin'
        filepaths = assemble_perseus_filepaths_by_type(text_type)
        jv_replacer = JVReplacer()
        text_cleaner = general_cleanup
        word_tokenizer = WordTokenizer('latin')
        if rm_stops:
            stops = latin_stops
        else:
            stops = None

    if lemmatize:
        lemmatizer = LemmaReplacer(language)

    sent_tokenizer = TokenizeSentence(language)

    length = len(filepaths)
    for filepath in filepaths:
        length = length - 1
        print(length)
        with open(filepath, encoding='utf-8') as f:
            text = f.read()
        # light first-pass cleanup, before sentence tokenization (which relies on punctuation)
        text = text_cleaner(text, rm_punctuation=False, rm_periods=False)
        sent_tokens = sent_tokenizer.tokenize_sentences(text)
        # doc_sentences = []
        for sentence in sent_tokens:
            # a second cleanup at sentence-level, to rm all punctuation
            sentence = text_cleaner(sentence, rm_punctuation=True, rm_periods=True)
            sentence = word_tokenizer.tokenize(sentence)
            sentence = [s.lower() for s in sentence]
            sentence = [w for w in sentence if w]
            if language == 'latin':
                sentence = [w[1:] if w.startswith('-') else w for w in sentence]

            if stops:
                sentence = [w for w in sentence if w not in stops]

            sentence = [w for w in sentence if len(w) > 1]  # rm short words

            if sentence:
                sentence = sentence

            if lemmatize:
                sentence = lemmatizer.lemmatize(sentence)
            if sentence and language == 'latin':
                sentence = [jv_replacer.replace(word) for word in sentence]
            if sentence:
                yield sentence
                # doc_sentences.append(sentence)
                # if doc_sentences != []:
                #    yield doc_sentences

def make_model(corpus, lemmatize=False, rm_stops=False, size=100, window=10, min_count=5, workers=4, sg=1, save_path=None):
    """Train W2V model."""

    # Simple training, with one large list
    t0 = time.time()

    sentences_stream = gen_docs(corpus, lemmatize=lemmatize, rm_stops=rm_stops)
    # sentences_list = []
    # for sent in sentences_stream:
    #    sentences_list.append(sent)

    model = Word2Vec(sentences=list(sentences_stream), size=size, window=window, min_count=min_count, workers=workers,
                     sg=sg)

    # "Trim" the model of unnecessary data. Model cannot be updated anymore.
    model.init_sims(replace=True)

    if save_path:
        save_path = os.path.expanduser(save_path)
        model.save(save_path)

if __name__ == '__main__':
    print(assemble_perseus_author_filepaths())