# LATIN_FINALS
Using the cltk library to try to expand the range of corpora which can be converted into a word2vec model.

[Presentation (Russian)](https://docs.google.com/presentation/d/148UNR7Y-TNGGy054cfxVNL-sf7HUx6H5woPhfZta3Mg/edit?usp=sharing)

## Files

**main.py**: compares the words NIGER and FURVUS using the Word2Vec model based on Perseus.

**perseus_word2vec.py**: contains different cltk functions, modified for being able to make models with some corpora other than phi5 and tlg

**makemodel.py**: makes models based on several Perseus' subcorpora (not initiated properly (yet))

## Models

### Ignis

**ignis_poetry.model**: poetry

**ignis_prose.model**: prose

### Perseus

**perseus.model**: the whole Perseus corpus

**late_silver.model**: the late_silver subcorpus

**old.model**: the old subcorpus

### On their way

* **early_silver.model**
* **christian.model**
* **augustan.model**

**THIS WORKS ONLY IF YOU HAVE CLTK AND THE CLTK_DATA FOLDER INSTALLED**
