"""
NeoSoft RapidPhish - the simple, rapid, and offline phishing blocker

Copyright NeoSoft 2018-2024. All rights reserved. This software is copyrighted
work and should not be distributed outside the allowed areas.
"""

from urllib.parse import urlparse
import jellyfish
import time
import hashlib
import json

# Official Discord domains to compare the given URLs against
discord_urls = ['discord.gg', 'discord.com', 'discord.gift', 'discord.gifts', 'discordapp.com', 'dis.gd',
                'steampowered.com', 'discordapp.net', 'discord.new', 'discordstatus.com']

# Not Discord domains, but safe troll sites that can be safely ignored
# Also contains common false positives
# If there is no TLD, then it is considered as a keyword
whitelist = ['discordgift.site', 'dlscord.life', 'l.discord.ski', 'dis.cord.gifts',
             'skribbl.io', 'dsc.gg', 'discord.py', 'disboard']

# Official Discord domains without the TLDs
real_url_names = ['discord', 'discordapp']

# 100% positives - ban these URLs
# Does not override whitelist
blacklist = ['disboard.com']

try:
    discord_bl = json.loads(open('hashes.json', 'r', encoding='utf-8').read())
except:
    discord_bl = {}


def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature


class RapidPhishScan(object):
    def __init__(self, data):
        self.domain = data['domain']
        self.similarity = data['similarity']
        self.type = data['type']
        self.positive = data['positive']


class RapidPhishResult(object):
    def __init__(self, data):
        self.url = data['url']
        self.verdict = data['verdict']
        self.whitelist = data['whitelist_or_real']
        self.scans = data['scans']
        try:
            self.blacklist = data['in_blacklist']
        except:
            self.blacklist = False


class RapidPhishResults(object):
    def __init__(self, results, priority, duration):
        self.results = results
        self.priority = priority
        self.duration = duration
        if priority == None:
            self.final_verdict = 'safe'
        else:
            self.final_verdict = 'unsafe'


def compare_urls(urls, threshold, custom_blacklist=[], custom_whitelist=[]):
    '''Compares a list of URLs against official Discord domains.'''
    results = []
    real_urls = discord_urls + custom_blacklist
    count = 0
    start = time.time()
    for url in urls:
        if not url.startswith('https://') and not url.startswith('http://'):
            urls[count] = f'http://{url}'
        count += 1

    for url in urls:
        t = urlparse(url).netloc
        repeat = url.count('.')
        if t in whitelist or t in real_urls or t in custom_whitelist:
            results.append(RapidPhishResult({'url': url, 'verdict': 'safe', 'whitelist_or_real': True,
                                             'scans': {'full': [], 'nosubd': [], 'nontld': []}}))
        else:
            t_hash = encrypt_string(t)
            if t_hash in discord_bl:
                results.append(RapidPhishResult({'url': url, 'verdict': 'unsafe', 'whitelist_or_real': False,
                                                 'scans': {'full': [], 'nosubd': [], 'nontld': []},
                                                 'in_blacklist': True}))
                continue

            verdict = 'safe'
            result = []
            if repeat > 1:
                t1 = '.'.join(t.split('.')[1:])
                if t1 in real_urls:
                    results.append(RapidPhishResult({'url': url, 'verdict': 'safe', 'whitelist_or_real': True,
                                                     'scans': {'full': [], 'nosubd': [], 'nontld': []}}))
                    continue
            else:
                pass

            for domain in real_urls:
                similarity = jellyfish.jaro_similarity(t, domain)
                if similarity >= threshold and not similarity == 1:
                    verdict = 'unsafe'
                    result.append(
                        RapidPhishScan({'domain': domain, 'similarity': similarity, 'type': 'full', 'positive': True}))
                else:
                    result.append(
                        RapidPhishScan({'domain': domain, 'similarity': similarity, 'type': 'full', 'positive': False}))

            if repeat > 1:
                t = '.'.join(t.split('.')[1:])
            else:
                pass

            t_hash = encrypt_string(t)
            if t_hash in discord_bl:
                results.append(RapidPhishResult({'url': url, 'verdict': 'unsafe', 'whitelist_or_real': False,
                                                 'scans': {'full': [], 'nosubd': [], 'nontld': []},
                                                 'in_blacklist': True}))
                continue

            for url in blacklist:
                if url in t:
                    results.append(RapidPhishResult({'url': url, 'verdict': 'unsafe', 'whitelist_or_real': False,
                                                     'scans': {'full': [], 'nosubd': [], 'nontld': []},
                                                     'in_blacklist': True}))
                    continue

            for domain in real_urls:
                similarity = jellyfish.jaro_similarity(t, domain)
                if similarity >= threshold and not similarity == 1:
                    verdict = 'unsafe'
                    result.append(RapidPhishScan(
                        {'domain': domain, 'similarity': similarity, 'type': 'nosubd', 'positive': True}))
                else:
                    result.append(RapidPhishScan(
                        {'domain': domain, 'similarity': similarity, 'type': 'nosubd', 'positive': False}))

            t2 = t.split('.')[0]
            if t2 in whitelist:
                results.append(RapidPhishResult({'url': url, 'verdict': 'safe', 'whitelist_or_real': True,
                                                 'scans': {'full': [], 'nosubd': [], 'nontld': []}}))
                continue

            for domain in real_urls:
                similarity = jellyfish.jaro_similarity(t2, url)
                if similarity >= threshold and not similarity == 1:
                    verdict = 'unsafe'
                    result.append(RapidPhishScan(
                        {'domain': domain, 'similarity': similarity, 'type': 'nontld', 'positive': True}))
                else:
                    result.append(RapidPhishScan(
                        {'domain': domain, 'similarity': similarity, 'type': 'nontld', 'positive': False}))

            results.append(
                RapidPhishResult({'url': url, 'verdict': verdict, 'whitelist_or_real': False, 'scans': result}))

    priority = None
    for result in results:
        if result.verdict == 'unsafe':
            priority = result

    end = time.time()
    elapsed = end - start

    return RapidPhishResults(results, priority, elapsed)