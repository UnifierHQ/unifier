import re
import unicodedata
import jellyfish
import time
from tld import get_tld
from utils.base_filter import FilterResult, BaseFilter, FilterConfig
from utils import rapidphish

# Common spam/phishing content
# If a message contains ALL of the keywords in any of the entries, the Filter will flag it.
suspected = [
    ['nsfw', 'discord.'], # Fake NSFW server
    ['onlyfans', 'discord.'], # Fake NSFW server 2
    ['18+', 'discord.'], # Fake NSFW server 3
    ['leak', 'discord.'], # Fake NSFW/game hacks server
    ['dm', 'private', 'mega', 'links'], # Mega links scam
    ['dm', 'private', 'mega', 'links', 'adult'], # Mega links scam 2
    ['get started by asking (how)', 't.me'], # Investment scam (Telegram edition)
    ['get started by asking (how)', '+1'], # Investment scam (Whatsapp edition)
    ['only interested people should', 't.me'], # Investment scam (Telegram edition 2)
    ['only interested people should', '+1'], # Investment scam (Whatsapp edition 2)
    ['gift', '[steamcommunity.com'], # Steam gift card scam
    ['gift', '[steampowered.com'], # Steam gift card scam 2
    ['@everyone', '@everyone'], # Mass ping filter
    ['@everyone', '@here'], # Mass ping filter 2
    ['@here', '@here'], # Mass ping filter 3
    ['executor', 'roblox'], # Roblox exploits scam
    ['hack', 'roblox'], # Roblox exploits scam 2
    ['exploit', 'roblox'], # Roblox exploits scam 3
    ['uttp', 'uttp'], # UTTP raiders filter (ew.)
]

# Common spam/phishing content (case sensitive)
suspected_cs = [
    ['RAID', 'RAID'], # Raid filter
    ['FORCES', 'FORCES'], # "Egocentric raiders who think they're the feds or some shit" filter
]

# Commonly abused services
# These services aren't necessarily malicious, but spammers like to use them.
abused = [
    't.me',
    'telegram.me',
    'telegram.org',
    'mega.nz'
]

def uppercase_ratio(text):
    letters = [char for char in text if char.isalpha()]
    capitals = [char for char in letters if char.isupper()]
    if not letters:
        return 0, 0
    return (len(capitals) / len(letters)), len(letters)

def bypass_killer(string):
    if not [*string][len(string) - 1].isalnum():
        return string[:-1]
    else:
        return None

def get_urls(content):
    # Stage 1: Use regex to find URLs
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, content)
    urls = [x[0].lower() for x in url]

    # Stage 2: Detect URLs from hyperlinks and possible bypasses
    filtered = content.replace('\\', '').lower()
    for url in urls:
        # Remove already found URLs so we don't end up with duplicates
        filtered = filtered.replace(url, '', 1)

    for word in filtered.split():
        # Stage 2.1: Detect URLs from hyperlinks
        if '](' in word:
            if word.startswith('['):
                word = word[1:]
            if word.endswith(')'):
                word = word[:-1]
            word = word.replace(')[', ' ')
            words = word.split()
            found = False
            for word2 in words:
                words2 = word2.replace('](', ' ').split()
                for word3 in words2:
                    if '.' in word3:
                        if not word3.startswith('http://') or not word3.startswith('https://'):
                            word3 = 'http://' + word3
                        while True:
                            try:
                                word3 = bypass_killer(word3)
                                if word3 is None:
                                    break
                            except:
                                break
                        if len(word3.split('.')) == 1:
                            continue
                        else:
                            if word3.split('.')[1] == '':
                                continue
                        try:
                            get_tld(word3.lower(), fix_protocol=True)
                            if '](' in word3.lower():
                                word3 = word3.replace('](', ' ', 1).split()[0]
                            urls.append(word3.lower())
                            found = True
                        except:
                            pass

            if found:
                # Hyperlink successfully found
                continue

        # Stage 2.2: Detect hyperlinks from possible bypasses
        if '.' in word:
            while True:
                # I forgot how this works, but it works I guess
                try:
                    word_filtered = bypass_killer(word)
                    if word_filtered is None:
                        break
                except:
                    break

                word = word_filtered

            if len(word.split('.')) == 1:
                continue
            else:
                if word.split('.')[1] == '':
                    continue
            try:
                get_tld(word.lower(), fix_protocol=True)
                if '](' in word.lower():
                    word = word.replace('](', ' ', 1).split()[0]
                urls.append(word.lower())
            except:
                pass

    # Stage 3: Add missing protocols
    for index in range(len(urls)):
        url = urls[index]
        if not url.startswith('http://') or not url.startswith('https://'):
            urls[index] = 'https://' + url

    return urls

def check_patterns(text, patterns):
    for entry in patterns:
        match = True
        working_with = str(text)
        for keyword in entry:
            if keyword in working_with:
                working_with = working_with.replace(keyword, '', 1)
            else:
                match = False
                break
        if match:
            return True

    return False

class Filter(BaseFilter):
    def __init__(self):
        super().__init__(
            'spam',
            'Suspected Spam Filter',
            'Multi-stage filter that detects and blocks spam and some phishing attacks.'
        )

        self.add_config(
            'abused', FilterConfig(
                'Block frequently abused services',
                'Services commonly abused by spammers on Discord (such as Telegram) will be blocked.',
                'boolean',
                default=False
            )
        )
        self.add_config(
            'repeated', FilterConfig(
                'Block repeated messages',
                'Messages that are identical or similar to previous messages will be blocked.',
                'boolean',
                default=False
            )
        )
        self.add_config(
            'repeated_threshold', FilterConfig(
                'Repeated messages similarity threshold',
                'Messages that have similarity above this threshold will be considered repeated.',
                'float',
                default=0.85,
                limits=(0.5,1)
            )
        )
        self.add_config(
            'repeated_length', FilterConfig(
                'Repeated messages length threshold',
                'Only messages with length above this threshold will be checked for repetition.',
                'integer',
                default=10,
                limits=(5, 2000)
            )
        )
        self.add_config(
            'repeated_count', FilterConfig(
                'Repeated messages count threshold',
                'Messages repeated more than this amount of times will be considered spam.',
                'integer',
                default=5
            )
        )
        self.add_config(
            'repeated_timeout', FilterConfig(
                'Repeated messages timeout',
                'Repetition count will be reset after this number of seconds.',
                'integer',
                default=30
            )
        )

    def check(self, message, data) -> FilterResult:
        content_normalized = unicodedata.normalize('NFKD', message['content'])
        content = content_normalized.lower()

        # Detect spam from common patterns
        is_spam = check_patterns(content, suspected) or check_patterns(content_normalized, suspected_cs)

        # Detect spam from uppercase ratio
        ratio, count = uppercase_ratio(content_normalized)
        if ratio > 0.75 and count > 60:
            is_spam = True

        # Use RapidPhish to detect possible phishing URLs
        if not is_spam:
            urls = get_urls(content)
            if len(urls) > 0:
                # Best threshold for this is 0.85
                results = rapidphish.compare_urls(
                    urls, 0.85, custom_blacklist=abused if data['config'].get('abused', False) else None
                )
                is_spam = results.final_verdict == 'unsafe' or is_spam

        if data['config'].get('repeated', False) and len(content) > data['config'].get('repeated_length', 10):
            phrases = data['data'].get(message['server'], [])
            has_phrase = False

            for index in range(len(phrases)):
                phrase = phrases[index]
                similarity = jellyfish.jaro_similarity(phrase["content"], content)  # pylint: disable=E1101
                if similarity > data['config'].get('repeated_threshold', 0.85):
                    has_phrase = True
                    phrases[index]["count"] += 1
                    phrases[index]["reset"] = round(time.time()) + data['config'].get('repeated_timeout', 30)

                    if phrases[index]["count"] > data['config'].get('repeated_count', 5):
                        is_spam = True
                        break

            # Add phrase if needed
            if not has_phrase:
                phrases.append({
                    "content": content,
                    "count": 1,
                    "reset": round(time.time()) + data['config'].get('repeated_timeout', 30)
                })

            data['data'].update({message['server']: phrases})

        return FilterResult(
            not is_spam, data, message='Message is likely spam.', should_log=True, should_contribute=True
        )
