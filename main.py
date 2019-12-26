import gensim
from pprint import pprint

model = gensim.models.Word2Vec.load('late_silver.model')
color_list = [('niger', 'furuus')]

def print_info_one_word(word):
    print(word.upper()+':')
    print()
    for info in model.most_similar(word):
        print(info)
    print()

def print_info_two_words(tup):
    word1 = tup[0]
    word2 = tup[1]
    print(f'{word1.upper()} & {word2.upper()}:')
    print()
    print('COSINE SIMILARITY:', model.similarity(word1, word2))
    print()
    print_info_one_word(word1)
    print_info_one_word(word2)
    print()

if __name__ == '__main__':
    for color_pair in color_list:
        print_info_two_words(color_pair)