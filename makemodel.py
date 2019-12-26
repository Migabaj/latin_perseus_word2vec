from perseus_word2vec import make_model
import os

filepath = os.path.expanduser('~/LATIN_FINALS/late_silver.model')
print(filepath)
types_and_paths = ['early_silver', 'christian', 'old', 'republican']

if __name__ == '__main__':
    for t_a_p in types_and_paths:
        make_model(f'perseus.{t_a_p}', lemmatize=True, rm_stops=True, size=100, window=30, min_count=5,
                   workers=4, sg=0, save_path=os.path.expanduser(f'~/LATIN_FINALS/{t_a_p}.model'))