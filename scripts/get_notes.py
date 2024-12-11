import sys

version = sys.argv[1]

try:
    file = open(f'release-notes/{version}.md', 'r', encoding='utf-8')
    print(file.read())
    file.close()
except:
    print('There are no release notes for this version.')
