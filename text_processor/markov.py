#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import re
import random
import os

import markovify
import spacy

nlp = spacy.load('en_core_web_sm')

class POSifiedText(markovify.Text):
    def word_split(self, sentence):
        return ["::".join((word.orth_, word.pos_)) for word in nlp(sentence)]

    def word_join(self, words):
        # sentence = " ".join(word.split("::")[0] for word in words)
        sentence = ''
        for w in words:
            word, type = w.split("::")
            if type != 'PUNCT' and not word.startswith('\'') and sentence:
                sentence += ' '
            sentence += word
        return sentence


class Impersonator:
    random.seed()

    def __init__(self, person, text, state_size=3, load=False):
        self.person = ' '.join(person)
        folder_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'store')
        file_path = os.path.join(folder_path, self.person)

        self._sentences = None

        if load and os.path.exists(file_path):
            with open(file_path, 'r') as f:
                self.markov = POSifiedText.from_json(f.read())
        else:
            self.markov = POSifiedText(text, state_size=state_size)
            if not os.path.isdir(folder_path):
                os.makedirs(folder_path)
            with open(file_path, 'w') as f:
                f.write(self.markov.to_json())

    @property
    def sentence(self):
        return self.sentence

    @sentence.getter
    def sentence(self):
        if not self._sentences:
            print('Generating sentences...')
            sentences = [self.markov.make_sentence(max_overlap_ratio=0.5,
                                                   max_overlap_total=10)
                         for _ in range(200)]
            self._sentences = [s for s in sentences if s]

        return self._sentences.pop()

