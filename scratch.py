#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from collections import defaultdict
from pprint import pprint

from downloader.download import EpisodeIndex
from text_processor.markov import Impersonator

ei = EpisodeIndex('Reply All')
ei.get_episodes()

all_text = defaultdict(list)
for ep in ei.episodes:
    print(ep.title)
    print(sorted(ep.transcript.by_user.keys(), key=lambda x: x[0]))
    for person, text in ep.transcript.by_user.items():
        all_text[person].extend(text)


use_existing = not any(ep.new for ep in ei.episodes)

for k, v in all_text.items():
    if len(v) > 500:
        imp = Impersonator(person=k, text=v, load=use_existing)
        for _ in range(10):
            print(imp.person, '-', imp.sentence)