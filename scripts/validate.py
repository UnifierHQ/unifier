import sys
import os

data = {
    'type': sys.argv[1],
    'staging': sys.argv[2]
}

# arguments to validate
validation = {
    'type': {
        'require_all': True,
        'strategy': {
            'explicit': ['alpha', 'beta', 'stable']
        }
    },
    'staging': {
        'require_all': True,
        'strategy': {
            'explicit': [True, False]
        }
    }
}

invalid = False

for arg, value in data.items():
    passed = 0
    strategies = len(validation[arg]['strategy'].keys())
    require_all = validation[arg]['require_all']
    if len(validation[arg]['strategy']) == 0:
        # no validation here, mark as passed
        passed += 1
        continue

    for strategy in validation[arg]['strategy']:
        if strategy == 'explicit':
            # value must match one of the given values

            if value in validation[arg]['strategy']['explicit']:
                passed += 1
        elif strategy == 'range':
            # value must fit within a given range

            if type(value) is str:
                # check string length
                if validation[arg]['strategy']['range'][0] <= len(value) <= validation[arg]['strategy']['range'][1]:
                    passed += 1
            elif type(value) is int or type(value) is float:
                # check value
                if validation[arg]['strategy']['range'][0] <= value <= validation[arg]['strategy']['range'][1]:
                    passed += 1
        else:
            # mark as passed anyways as we can't validate the input with an unknown strategy

            passed += 1

    if require_all and passed < strategies:
        invalid = True
        print(f'Value of {arg} failed validation check.')

if invalid:
    sys.exit(1)

env_file = os.getenv('GITHUB_ENV')

with open(env_file, "a") as myfile:
    myfile.write(f"STAGING=" + ("true" if data['staging'] else "false") + '\n')
