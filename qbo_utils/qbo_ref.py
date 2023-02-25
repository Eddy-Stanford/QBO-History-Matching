import requests
import tempfile
import os 
from fub_qbo_file import FUBDataFile
import numpy as np


FUB_DATA_URL = "https://www.geo.fu-berlin.de/met/ag/strat/produkte/qbo/qbo.dat"


def fetch_qbo_file(url=FUB_DATA_URL,local_path=None) -> FUBDataFile:
    if local_path and os.path.isfile(local_path):
        return FUBDataFile(local_path)
    response = requests.get(url)
    if response.status_code == 200:
        if local_path: 
            with open(local_path,'wb') as f:
                f.write(response.content)
            return FUBDataFile(local_path)
        else:
            file = tempfile.NamedTemporaryFile(mode='w+',encoding='utf-8')
            file.write(response.text)
            return FUBDataFile(file=file)
