from nltk.corpus import wordnet as wn
import os
import numpy as np
import pickle as plk
import random
import scipy.spatial.distance
import pandas as pd
import gensim.models as gm

from scipy.stats import entropy
from numpy.linalg import norm
from gensim.test.utils import datapath, get_tmpfile
from gensim.models import KeyedVectors
from gensim.scripts.glove2word2vec import glove2word2vec
from tempfile import TemporaryFile

import sklearn.metrics
from sklearn.metrics import pairwise_distances
from sklearn.metrics.pairwise import pairwise_kernels

import heapq
from sklearn.preprocessing import normalize
import logging
import gensim


class WER(object):
    '''
    '''

    def __init__(self, path='Embeddings/', embedings_size=300, type='GloVe', log=''):
        '''

        :param path:
        :param embedings_size:
        :param type:
        :param log: name of the log filer

        :var embeddings_index:
        :var words:
        :var filtered_words:
        :var synonims:
        :var synonimsDistribution:
        :var random_words_pairs:
        :var randomDistribution:
        :var synonimsDistributionComplementary:
        :var auxiliar_list: list empty prepare for save auxilar data if necessary DEBE DESAPARECER PRONTO MUHAHAHAHA
        :var antonims:
        :var antonimsDistribution:
        :var wordSynset: [(word, [synsets it belongs to])]
        :var embedding_name:

        :func filterWN:
        :func wordSynsetConstruct:
        :func norm:
        :func randomDistances:
        :func randomDistancesList:
        :func pureSynonyms:
        :func pureAntonyms:
        :func antonymsFilteredWords:
        :func synonymsFilteredWords:
        :func synonymsComplementary:
        :func randomFilteredWords:
        :func non_filtered_randomWords:
        :func returnSinonyms:
        :func distancesBetweenSet:
        :func notVocabularyDistribution:
        :func nearestNeighbour:
        :func clearArrayOfArrays:
        :func arrayOfArraysToArray:
        :func saveWords:
        :func loadWords:
        :func saveData:
        :func loadData:
        :func saveEmbedding:
        :func loadEmbeddingDict:
        :func test:
        :func __str__:
        :func __repr__:
        '''

        allowed_types = {'GloVe':1,
                         'Word2Vec':2}

        self.path = path
        self.embedings_size = embedings_size
        self.type = allowed_types[type]
        self.embeddings_index = {}
        self.words = []
        self.filtered_words = []
        self.synonims = []
        self.synonimsDistribution = []
        self.random_words_pairs = []
        self.randomDistribution = []
        self.synonimsDistributionComplementary = []
        self.synonimsComplementary = []
        self.auxiliar_list = []
        self.antonims = []
        self.antonimsDistribution = []
        self.wordSynset = []

        ## inicializamos el logger
        logger_name = log

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(logger_name + '.log')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # GLOVE
        # =====
        if self.type == 1:

            self.embedding_name = 'glove.6B.' + str(self.embedings_size) + 'd.txt'
            f = open(os.path.join(self.path, self.embedding_name))

            for line in f:
                values = line.split()
                word = values[0]
                coefs = np.asarray(values[1:], dtype='float32')
                self.embeddings_index[word] = coefs

            f.close()
            self.words = list(self.embeddings_index.keys())

            self.logger.info('-. GloVe embedding .-')

        # WORD2VEC
        # ========
        elif self.type == 2:
            self.model = gensim.models.KeyedVectors.load_word2vec_format(path + 'GoogleNews-vectors-negative300.bin.gz', binary=True)
            self.words = list(self.model.vocab)

            self.logger.info('-. Word2Vec embedding .-')

        else:
            print('ERROR')
            self.logger.info('FATAL ERROR, the embedding has not been charged')


    def norm(self, vector, vector2, norma=1):
        '''

        :param vector:
        :param vector2:
        :param norma:
        :return: value of the distence (under the selected norm) between the
                 two vectors
        '''


        if norma == 1 or norma is "euclidean":
            calculo = vector
            for i in range(0, len(vector)):
                calculo[i] = calculo[i] - vector2[i]
            suma = 0
            for i in calculo:
                suma += np.power(i, 2)
            value = np.sqrt(suma)
        elif norma == 2 or norma is "cosine":
            value = scipy.spatial.distance.cosine(vector, vector2)

        elif norma == 3 or norma is "cityblock":
            value = scipy.spatial.distance.cityblock(vector, vector2)

        elif norma == 4 or norma is "l1":
             value = np.linalg.norm((vector - vector2), ord=1)

        elif norma == 7 or norma is "chebyshev":
            value = scipy.spatial.distance.chebyshev(vector, vector2)

        elif norma == 8 or norma is "minkowski":
            value = scipy.spatial.distance.minkowski(vector, vector2)

        elif norma == 9 or norma is "sqeuclidean":
            value = scipy.spatial.distance.sqeuclidean(vector, vector2)

        elif norma == 10 or norma is "jensenshannon":
            _P = vector / norm(vector, ord=1)
            _Q = vector2 / norm(vector2, ord=1)
            _M = 0.5 * (_P + _Q)
            value =  0.5 * (entropy(_P, _M) + entropy(_Q, _M))

        elif norma == 12 or norma is "jaccard":
            sklearn.metrics.jaccard_similarity_score(vector, vector2)

        elif norma == 13 or norma is "correlation":
            value = scipy.spatial.distance.correlation(vector, vector2)

        elif norma == 14 or norma is "braycurtis":

            value = scipy.spatial.distance.braycurtis(vector, vector2)

        elif norma == 15 or norma is "canberra":
            value = scipy.spatial.distance.canberra(vector, vector2)

        elif norma == 16 or norma is "kulsinski":
            value = scipy.spatial.distance.cdis(vector, vector2)

        elif norma == 17 or norma is "max5":
            # take the sum of the 5 maximun diference dimensions
            v = vector2 - vector
            v2 = [abs(x) for x in v]
            aux = heapq.nlargest(5, v2)
            value = sum(aux)

        elif norma == 18 or norma is "max10":
            # take the sum of the 10 maximun diference dimensions
            v = vector2 - vector
            v2 = [abs(x) for x in v]
            aux = heapq.nlargest(10, v2)
            value = sum(aux)


        elif norma == 19 or norma is "max25":
            # take the sum of the 25 maximun diference dimensions
            v = vector2 - vector
            v2 = [abs(x) for x in v]
            aux = heapq.nlargest(25, v2)
            value = sum(aux)

        elif norma == 20 or norma is "max50":
            # take the sum of the 50 maximun diference dimensions
            v = vector2 - vector
            v2 = [abs(x) for x in v]
            aux = heapq.nlargest(50, v2)
            value = sum(aux)

        elif norma == 21 or norma is "max100":
            # take the sum of the 100 maximun diference dimensions
            v = vector2 - vector
            v2 = [abs(x) for x in v]
            aux = heapq.nlargest(100, v2)
            value = sum(aux)

        elif norma == 28:
            non_sing_changes = 0

            for i in range(0, len(vector)):
                if vector[i] >= 0 and vector2[i] >= 0:
                    non_sing_changes += 1
                if vector[i] < 0 and vector2[i] < 0:
                    non_sing_changes += 1

            value = len(vector) - non_sing_changes

        else:
            value = 0

        return value

    def returnVector(self, setOfWords = []):
        '''

        :param setOfWords:
        :return:
        '''

        setOfArrays = [] # cqmbiar nombre en el futuro, este conjunto no es un set si no un array

        # GloVe
        # =====
        if self.type == 1:
            for word in setOfWords:
                setOfArrays.append(self.embeddings_index[word])

        # Word2Vec
        # ========
        elif self.type == 2:
            for word in setOfWords:
                setOfArrays.append(self.model.get_vector(word))
        else:
            pass

        return setOfArrays

    def filterWN(self):
        '''
        Filtramos por wordnet
        :return: None
        '''
        self.logger.info('Starting filtrated with WordNet')
        wn_lemmas = set(wn.all_lemma_names())
        for j in self.words:
            if j in wn_lemmas:
                self.filtered_words.append(j)

        self.filtered_words = list(set(self.filtered_words))
        self.logger.info('Finished filtrated with WordNet')

    def randomDistances(self, words, number=5000, all=False, norma=1):
        '''

        :param words:
        :param number:
        :param all: boolean, if True then take as many random distances as elements
                    has the set.
        :param norma:
        :return:
        '''

        self.logger.info("Start taking random distances")
        distancias = []

        pairs = []
        # GloVe
        # =====
        if self.type == 1:
            if all:
                number = len(words)

            for i in range(1, number - 1):
                secure_random = random.SystemRandom()
                pairs.append((secure_random.choice(words), secure_random.choice(words)))

            for j in range(0, number - 1):
                try:
                    distancia = self.norm(vector=self.embeddings_index[words[j]],
                                          vector2=self.embeddings_index[words[j + 1]], norma=norma)
                    distancias.append(distancia)
                except Exception as e:
                    print (e)
                    distancias.append(0)
                    pass

        # Word2Vec
        # ========
        elif self.type == 2:
            if all:
                number = len(words)

            for i in range(1, number - 1):
                secure_random = random.SystemRandom()
                pairs.append((secure_random.choice(words), secure_random.choice(words)))

            for j in range(0, number - 1):
                try:
                    distancia = self.norm(vector=self.model.get_vector(words[j]),
                                          vector2=self.model.get_vector(words[j + 1]), norma=norma)
                    distancias.append(distancia)
                except Exception as e:
                    print (e)
                    distancias.append(0)
                    pass

        else:
            pass

        self.logger.info("Finished random distances")
        return distancias

    def randomDistancesList(self, list, norma=1):
        '''

        :param lista:
        :param number:
        :param all:
        :param norma:
        :return: array with distances between elements of the sets in the given
                 set
        '''

        distancias = []

        # GloVe
        # =====
        if self.type == 1:
            for conjunto_sinonimos in list:
                conjunto_sinonimos = list(set(conjunto_sinonimos))
                for i in range(0, len(conjunto_sinonimos)):
                    if i + 1 < len(conjunto_sinonimos):
                        try:
                            distancia = self.norm(vector=self.embeddings_index[conjunto_sinonimos[i]],
                                                  vector2=self.embeddings_index[conjunto_sinonimos[i + 1]], norma=norma)
                            distancias.append(distancia)
                        except Exception as e:
                            print(e)
                            distancias.append(0)
                            pass

        # Word2Vec
        # ========
        elif self.type == 2:
            for conjunto_sinonimos in lista:
                conjunto_sinonimos = list(set(conjunto_sinonimos))
                for i in range(0, len(conjunto_sinonimos)):
                    if i + 1 < len(conjunto_sinonimos):
                        try:
                            distancia = self.norm(vector=self.model.get_vector(conjunto_sinonimos[i]),
                                                  vector2=self.model.get_vector(conjunto_sinonimos[i + 1]), norma=norma)
                            distancias.append(distancia)
                        except Exception as e:
                            print(e)
                            distancias.append(0)
                            pass
        else:
            pass


        self.logger.info('Finished random distances in the array of arrays')
        return distancias

    def pureSynonyms(self):
        '''
        Compute the set of synonims, without distances
        :return: None
        '''
        conjunto = []
        for target_word in self.filtered_words:
            synsets = wn.synsets(target_word)
            for synset in synsets:
                auxiliar = []
                lemmas = synset.lemmas()
                numberSynom = len(lemmas)
                if numberSynom > 1:
                    for lemma in lemmas:
                        palabra = lemma.name()
                        if palabra in self.filtered_words:
                            auxiliar.append(palabra)
            conjunto.append(auxiliar)

            for conjuntito in conjunto:
                if len(conjuntito) == 0:
                    conjunto.remove(conjuntito)

        self.synonims = conjunto

    def pureAntonyms(self):
        '''
        Just compute the set of synonims, without distances
        :return: None
        '''

        conjunto = []
        for target_word in self.filtered_words:
            synsets = wn.synsets(target_word)
            for synset in synsets:
                auxiliar = []
                lemmas = synset.lemmas()
                numberSynom = len(lemmas)
                if numberSynom > 1:
                    for lemma in lemmas:
                        if lemma.antonyms():
                            antonimo = lemma.antonyms()[0].name()
                            if antonimo in self.filtered_words:
                                auxiliar.append(target_word)  # new line
                                auxiliar.append(antonimo)
            conjunto.append(auxiliar)

            for conjuntito in conjunto:
                if len(conjuntito) == 0:
                    conjunto.remove(conjuntito)

        self.antonims = conjunto

    def antonymsFilteredWords(self, norma = 1):
        '''
        Fills the antonimsDistribution array (from antonims set)
        :param norma:
        :return: None
        '''

        self.pureAntonyms() # self.antonims

        self.antonimsDistribution = self.randomDistancesList(self.antonims, norma = norma)

    def synonymsFilteredWords(self, norma=1):
        '''

        :param norma:
        :param number:
        :return: None
        '''

        conjunto = []
        for target_word in self.filtered_words:
            synsets = wn.synsets(target_word)
            for synset in synsets:
                auxiliar = []
                lemmas = synset.lemmas()
                numberSynom = len(lemmas)
                if numberSynom > 1:
                    for lemma in lemmas:
                        palabra = lemma.name()
                        if palabra in self.filtered_words:
                            auxiliar.append(palabra)
            conjunto.append(auxiliar)

            for conjuntito in conjunto:
                if len(conjuntito) == 0:
                    conjunto.remove(conjuntito)

        self.synonims = conjunto
        self.synonimsDistribution = self.randomDistancesList(lista=conjunto, norma=norma)

    def synonymsComplementary(self, norma=1, number=5000):
        '''
        Fill synonimsComplementary array and compute a random sample of their distribution
        :param norma:
        :param number:
        :return: None
        '''

        words_no_synomims = []
        for target_word in self.filtered_words:
            synsets = wn.synsets(target_word)
            for synset in synsets:
                lemas = synset.lemmas()
                numberSynom = len(lemas)
                if numberSynom == 1:
                    word = lemas[0].name()
                    if word in self.filtered_words:
                        words_no_synomims.append(p)

        words_no_synomims = list(set(words_no_synomims))
        self.synonimsComplementary = words_no_synomims

        self.synonimsDistributionComplementary = self.randomDistances(words=auxiliar, norma=norma, number=number)

    def randomFilteredWords(self, norma=1, number=5000, all=False):
        '''

        :param norma:
        :param number:
        :return:
        '''

        if all:
            self.randomDistribution = self.randomDistances(words=self.words, norma=norma, number=number)
        else:
            self.randomDistribution = self.randomDistances(words=self.filtered_words, norma=norma, number=number)


    def returnSinonyms(self, word):
        '''
        Returns and array of synonims of the word passed (based on WordNet)
        :param word: word whose synonims we want
        :return: array of synonims
        '''

        auxiliar = []

        for i in wn.synsets(word):
            vector_auxiliar = []
            for j in [x.name() for x in i.lemmas()]:
                vector_auxiliar.append(j)

            if len(vector_auxiliar) > 1:
                auxiliar.append(list(set(vector_auxiliar)))

        return auxiliar

    def distancesBetweenSet(self, norma=1, words=[]):
        '''
        Compute the distances between a word (the element 0 in the array) and a set of words.
        :param norma:
        :param words:
        :return: Array of arrays of words QUE PARARA SI EL ARRAY ES DE UN SOLO MODELO
        '''

        result = []
        # GloVe
        # =====
        if self.type == 1:
            for j in words:
                aux = []
                for i in j[1:]:
                    inicial = self.embeddings_index[i[0]]
                    try:
                        valor = self.norm(vector=inicial, vector2=self.embeddings_index[i], norma=norma)
                        aux.append(valor)
                    except KeyError:
                        pass

                result.append(aux)
        # Word2Vec
        # ========
        elif self.type == 2:
            for j in words:
                aux = []
                for i in j[1:]:
                    inicial = self.model.get_vector[i[0]]
                    try:
                        valor = self.norm(vector=inicial, vector2=self.model.get_vector[i], norma=norma)
                        aux.append(valor)
                    except KeyError:
                        pass

                result.append(aux)

        else:
            pass


        return (result)

    def notVocabularyDistribution(self, norma = 1):
        '''
        :param norma:
        :return: Return array of floats with the distributions of the words that
                 are not in the filtered group.
        '''

        conjunto_palabras = set(self.words) - set(self.filtered_words)

        return self.randomDistances(norma=norma, words=list(conjunto_palabras), number=10000)


    def wordSynsetConstruct(self):
        '''

        :return: None
        '''

        if len(self.filtered_words) == 0:
            self.filterWN()

        lista = []
        for j in self.words:
            words_synsets = wn.synsets(j)
            aux = []
            for i in words_synsets:
                aux.append(i.name())
            lista.append((j, aux))

        self.wordSynset = lista

    def nearestNeighbour(self, vector_words=[], norma=1, enviroment=[], num_results=1):
        '''
        Recives a word and compute the NN for it
        :param vector_words:
        :param norma:
        :param enviroment:
        :param num_results:
        :return: (word, closest words, distance to the closest one)
        '''

        #   PARECE NO FUNCIONAR PARA MAS DE UN RESULTADO

        wordsAndDistances = []

        if len(vector_words) != 0:
            for i in vector_words:
                iVector = self.embeddings_index[i]
                for j in enviroment:
                    jVector = self.embeddings_index[j]
                    jdistance = self.norm(vector=iVector, vector2=jVector, norma=norma)
                    wordsAndDistances.append((i, j, jdistance))
                    minimun = sorted(wordsAndDistances, key=lambda v: v[2])

        resultado = [(minimun[h][0], minimun[h][1], minimun[h][2]) for h
                     in
                     range(num_results)]

        return resultado

    @staticmethod
    def clearArrayOfArrays(data=[]):
        '''

        :param data:
        :return:
        '''
        logger.info("Starting clearArrayOfArrays")
        newData = []
        for i in data:
            auxiliar = []
            for j in i:
                if j != 0.0:
                    auxiliar.append(j)
            if len(auxiliar) != 0:
                newData.append(auxiliar)

        self.logger.info("Ended clearArrayOfArrays")
        return (newData)

    @staticmethod
    def arrayOfArraysToArray(data=[]):
        '''

        :param data:
        :return:
        '''
        logger.info("Starting arrayOfArraysToArray")
        resoult = []
        for i in data:
            for j in i:
                resoult.append(j)

        self.logger.info("Ended arrayOfArraysToArray")
        return (list(set(resoult)))

    def saveWords(self, name="saveWordsWithoutName"):
        '''
        Save lists of words in a pickle file
        :param name:
        :return: None
        '''

        self.logger.info('Starting saveWords')
        try:
            filename = name
            outfile = open(filename, 'wb')
            plk.dump(self.words, outfile)
            outfile.close()
        except Exception as e:
            print(e)
            pass
        self.looger.info('Finished saveWords')

    @staticmethod
    def loadWords(name="saveWordsWithoutName"):
        '''
        Load an array of words in pickle format
        :param name: name of the file
        :return: Array of strings
        '''
        self.logger.info("Starting laodWords")
        filename = name
        infile = open(filename, 'rb')
        data = plk.load(infile)
        infile.close
        self.looger.info("Ended loadWords")
        return (data)

    @staticmethod
    def saveData(option=1, name='saveDataWihoutName', data=[]):
        '''
        Save numerical data from the calculations in python or numpy formats
        :param option:
        :param name:
        :param data:
        :return: None
        '''

        if option == 1:

            filename = name
            outfile = open(filename, 'wb')
            plk.dump(data, outfile)
            outfile.close()

        elif option == 2:

            outfile = TemporaryFile()
            np.save(outfile, data)

        else:
            print('Error, please read the documentation of this function')
            pass

    @staticmethod
    def loadData(name="saveDataWithoutName"):
        '''
        Load a numeric array in pickle format
        :param name: name of the file
        :return: Array of numbers
        '''

        filename = name
        infile = open(filename, 'rb')
        data = plk.load(infile)
        infile.close()

        return (data)

    def saveEmbedding(self, name="saveEmbeddingWithoutName"):
        '''
        Save the words and their representations in a dictionary using pickle format
        :param name:
        :return: None
        '''

        data = {}
        for i in self.words:
            data[i] = self.embeddings_index[i]

        try:
            filename = name
            outfile = open(filename, 'wb')
            plk.dump(data, outfile)
            outfile.close()
        except Exception as e:
            print(e)
            pass

    @staticmethod
    def loadEmbeddingDict(name="saveEmbeddingWithoutName"):
        '''
        Load a dictionary, (word, representation_in_the_embedding)
        :param name: name of the file
        :return: Dictionary (str, Array of numbers)
        '''

        filename = name
        infile = open(filename, 'rb')
        data = plk.load(infile)
        infile.close()

        return (data)

    def __str__(self):
        '''
        :return:
        '''
        clase = type(self).__name__

    def __repr__(self):
        '''
        :return:
        '''

        clase = type(self).__name__

    def test(self):
        '''
        Test function
        :return: None
        '''
        print('It works!!')
        vector = [1, 1, 1, 1, 1, 1, 1, 1]
        vector2 = [1, 1, 1, 1, 1, 1, 100, 100]

        resoult2 = self.norm(vector=vector, vector2=vector2,
                             norma=2)
        print(resoult2)







# realizar unit testing and integration testing