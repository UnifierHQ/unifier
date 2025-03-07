"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2024-present  UnifierHQ

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# RapidPhish is a fast typosquatting detector made originally for the Nevira project.
# It is intended to be used to detect common scams on Discord.

from urllib.parse import urlparse
import jellyfish
import time
import hashlib

# Official domains to compare the given URLs against
discord_urls = [
    'discord.gg', 'discord.com', 'discord.gift', 'discord.gifts', 'discordapp.com', 'dis.gd', 'steampowered.com',
    'discordapp.net', 'discord.new', 'discordstatus.com', 'steamcommunity.com'
]

# Similar domains that can be safely ignored
whitelist = [
    'discordgift.site', 'dlscord.life', 'l.discord.ski', 'dis.cord.gifts', 'skribbl.io', 'dsc.gg', 'discord.py',
    'disboard'
]

# Official Discord domains without the TLDs
real_url_names = ['discord', 'discordapp']

# Known malicious sites
blacklist = [
    'disboard.com', 'spy.pet', 'spying.pet', 'spy.pm', 'steamecomnmunity.com'
]


def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature


class RapidPhishScan:
    def __init__(self, data):
        self.domain = data['domain']
        self.similarity = data['similarity']
        self.type = data['type']
        self.positive = data['positive']


class RapidPhishResult:
    def __init__(self, data):
        self.url = data['url']
        self.verdict = data['verdict']
        self.whitelist = data['whitelist_or_real']
        self.scans = data['scans']
        try:
            self.blacklist = data['in_blacklist']
        except:
            self.blacklist = False


class RapidPhishResults:
    def __init__(self, results, priority, duration):
        self.results = results
        self.priority = priority
        self.duration = duration
        if not priority:
            self.final_verdict = 'safe'
        else:
            self.final_verdict = 'unsafe'


def compare_urls(urls, threshold, custom_whitelist=None, custom_blacklist=None):
    """Compares a list of URLs against official Discord domains."""

    # Add missing lists
    if not custom_whitelist:
        custom_whitelist = []
    if not custom_blacklist:
        custom_blacklist = []

    results = []
    real_urls = discord_urls
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
                similarity = jellyfish.jaro_similarity(t, domain) # pylint: disable=E1101
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

            for blocked_url in blacklist + custom_blacklist:
                if blocked_url in t:
                    results.append(RapidPhishResult({'url': url, 'verdict': 'unsafe', 'whitelist_or_real': False,
                                                     'scans': {'full': [], 'nosubd': [], 'nontld': []},
                                                     'in_blacklist': True}))
                    continue

            for domain in real_urls:
                similarity = jellyfish.jaro_similarity(t, domain) # pylint: disable=E1101
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
                similarity = jellyfish.jaro_similarity(t2, url) # pylint: disable=E1101
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
