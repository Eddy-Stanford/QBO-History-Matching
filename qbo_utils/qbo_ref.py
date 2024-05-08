import os
import tempfile
from typing import Tuple

import numpy as np
import requests

from .fub_qbo_file import FUBDataFile
from .qbo_process import get_signal_period_amplitude

FUB_DATA_URL = "https://www.geo.fu-berlin.de/met/ag/strat/produkte/qbo/qbo.dat"
DEFAULT_TIMEOUT=120 # timeout in seconds
SUCCESS=200 # HTTP SUCCESS CODE

def fetch_qbo_file(url=FUB_DATA_URL, local_path=None) -> FUBDataFile:
    if local_path and os.path.isfile(local_path):
        return FUBDataFile(local_path).open()
    response = requests.get(url, timeout=DEFAULT_TIMEOUT)
    if response.status_code == SUCCESS:
        if local_path:
            with open(local_path, "wb") as f:
                f.write(response.content)
            return FUBDataFile(local_path).open()
        else:
            file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
            file.write(response.text)
            return FUBDataFile(file=file).open()


def get_reference_qbo(fub: FUBDataFile) -> Tuple[float, float, float, float]:
    data = fub.to_numpy()[:, -1]
    data = data[~np.isnan(data)]
    periods, amplitudes = get_signal_period_amplitude(data)
    return (
        np.mean(periods),
        np.std(periods) / np.sqrt(len(periods)),
        np.mean(amplitudes),
        np.std(amplitudes) / np.sqrt(len(amplitudes)),
    )
