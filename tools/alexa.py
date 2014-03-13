import json
import zipfile

from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen

config = None
top500 = []
url = urlopen('http://s3.amazonaws.com/alexa-static/top-1m.csv.zip')
f = ZipFile(BytesIO(url.read()))

for index, line in enumerate(f.open(f.infolist()[0]).readlines()):
    page = line.decode().split(',')[1].strip()

    if index == 500:
        break

    top500.append(page)

with open('../config.json') as f:
    config = json.load(f)

config["Pages"] = top500
with open('../config.json', 'w') as f:
    json.dump(config, f, indent=4)
