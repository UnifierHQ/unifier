import json
import os

with open('plugins/system.json', 'r') as file:
    data = json.load(file)

env_file = os.getenv('GITHUB_ENV')

if data['version'].startswith('v'):
    raw_version = data['version'][1:]
    version = data['version']
else:
    raw_version = data['version']
    version = data['version']

release = data['release']

with open(env_file, "a") as myfile:
    myfile.write(f"RAW_VERSION={raw_version}\nVERSION={version}\nRELEASE={release}")
