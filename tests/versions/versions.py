import requests  # Eventually when I get an API key i'll use it
import json

version_raw = open('tests/versions/example_version.json')
data = json.load(version_raw)

versions = [item['versionString'] for item in data['data']]


print(json.dumps(versions))
