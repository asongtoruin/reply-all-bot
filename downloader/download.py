#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from pprint import pprint
from collections import defaultdict

from bs4 import BeautifulSoup
import requests

NAME_REPLACEMENTS = {('AB', ''): ('ALEX', 'BLUMBERG'),
                     ('AG', ''): ('ALEX', 'GOLDMAN'),
                     ('PJ', ''): ('PJ', 'VOGT'),
                     ('DAMIANO', ''): ('DAMIANO', 'MARCHETTIE'),
                     ('PHIA', ''): ('PHIA', 'BENNIN'),
                     ('GOLDMAN', ''): ('ALEX', 'GOLDMAN'),
                     ('BLUMBERG', ''): ('ALEX', 'BLUMBERG'),
                     ('SRUTHI', ''): ('SRUTHI', 'PINNAMANENI')}


def safe_filename(name):
    out_name = name
    for char in '\/:*?"<>|':
        out_name = out_name.replace(char, '')
    return out_name + '.txt'


class EpisodeIndex:
    def __init__(self, show_name):
        # Prepare the show name for a url - no spaces, replaced with dashes
        parse_name = show_name.lower().replace(' ', '-')
        self.url = r'https://www.gimletmedia.com/{}' \
                   r'/all#all-episodes-list'.format(parse_name)
        self.show_name = show_name
        self.episodes = []

    def get_episodes(self):
        r = requests.get(self.url)
        soup = BeautifulSoup(r.text, 'html.parser')

        for ep in soup.find_all('div', class_='episode'):
            title = ep.find('h2').text
            if any(x in title.lower() for x in ('rebroadcast', 're-broadcast',
                                                'presents: ', 'introducing')):
                print('Skipping', title)
                continue
            episode = Episode(title=ep.find('h2').text,
                              partial_link=ep.find('a')['href'],
                              show=self.show_name)
            episode.get_transcript()
            if episode.transcript:
                self.episodes.append(episode)


class Episode:
    def __init__(self, show, title, partial_link):
        self.show = show
        self.title = title
        self.url = partial_link
        self.transcript = None
        self.new = False

    def __str__(self):
        return '{} Episode: {}'.format(self.show, self.title)

    @property
    def title(self):
        return self.__title

    @title.setter
    def title(self, title):
        self.__title = title

    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, partial_link):
        self.__url = r'https://www.gimletmedia.com' + partial_link

    def get_transcript(self):
        folder_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'cache', self.show)
        file_path = os.path.join(folder_path, safe_filename(self.title))
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            print('Downloading new episode:', self.title)
            r = requests.get(self.url)
            soup = BeautifulSoup(r.text, 'html.parser')
            web_transcript = soup.find('div', class_='episode-transcript collapsed')
            if not web_transcript:
                return None
            text = web_transcript.get_text('\n').upper()
            self.new = True

            # Write out the text
            if not os.path.isdir(folder_path):
                os.makedirs(folder_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text.encode('utf-8').decode('utf-8'))
        self.transcript = Transcript(text)


class Transcript:
    def __init__(self, text):
        self.text = text
        self.by_user = text

    @property
    def by_user(self):
        return self.__by_user

    @by_user.setter
    def by_user(self, text):
        # First, the input text is split according to its tabs
        first_split = text.replace('“', '"')\
                          .replace('”', '"') \
                          .replace('’', '\'') \
                          .replace(u'\xa0', u'\n') \
                          .split('\n')

        # This data still needs combining to pull out the speakers' names
        second_split = defaultdict(list)
        current_name = None
        for f in first_split:
            # name_match = re.match(r'^\s*([A-Z\s]*)\s*:(.*)', f)
            name_match = re.match(r'^\s*([^:]{,25})\s*:(.*)', f)
            if name_match:
                current_name = self.name_in_keys(name_match.group(1),
                                                 second_split)
                second_split[current_name].append(name_match.group(2).strip(' '))
            elif re.match(r'^\s*\[.*\]\s*$', f):
                pass
            elif f.lower() == 'credits':
                break
            else:
                if current_name and f:
                    second_split[current_name][-1] += ' ' + f.strip(' ')

        self.__by_user = second_split

    @staticmethod
    def name_in_keys(name, names_dict):
        split_name = tuple(name.split(' ')) if ' ' in name else (name, '')

        if split_name in NAME_REPLACEMENTS.keys():
            return NAME_REPLACEMENTS[split_name]

        for existing_name in names_dict.keys():
            if split_name[0] == existing_name[0] and \
                    (split_name[1] in ('TO', 'AND') or not split_name[1]):
                return existing_name
        return tuple(split_name)


if __name__ == '__main__':
    for show in ('Reply All',):#, 'Crimetown'):
        r = EpisodeIndex(show)
        r.get_episodes()


