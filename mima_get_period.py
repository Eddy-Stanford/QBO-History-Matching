import os 
import xarray as xr
import numpy as np
import pandas as pd
from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.fft import fft, fftfreq

DATADIR = "data"
FIVE_MONTHS = 5*30 

def get_qbo_period_fourier(data) -> float:
    omega = fft(data - np.mean(data))
    frequencies = fftfreq(len(data))
    imax = np.argmax(np.abs(omega))
    return 1/(30*frequencies[imax])

def get_qbo_period_transitions(data,t):
    
    interp = InterpolatedUnivariateSpline(t,data)
    roots = interp.roots()
    periods = roots[2::2] - roots[:-2:2]
    return periods.mean()/30,periods.std()/30,len(periods),roots

def get_qbo_rmse_amplitude(data):
    return np.sqrt(2*np.mean(data**2))

def get_qbo_amplitude(data,transitions):
    amplitudes = []
    for (start,stop) in zip(transitions[::2],transitions[2::2]):
        max = np.max(data[start:stop])
        min = np.min(data[start:stop])
        amplitudes.append((max-min)/2)
    return np.mean(amplitudes),np.std(amplitudes)

def rolling_average(data,n):
    return np.convolve(data,np.ones(n),mode='same')/n

if __name__ == '__main__':
    df = pd.read_csv(os.path.join(DATADIR,'paramlist.csv'),index_col='run_id')
    qbo_periods = [0]*100
    qbo_periods_std = [0]*100
    qbo_periods_fft = [0]*100
    qbo_count = [0]*100
    qbo_amplitude_rmse = [0]*100
    qbo_amplitude_mean = [0]*100
    qbo_amplitude_std = [0]*100
    for i in range(100):
        with xr.open_dataset(os.path.join(DATADIR,f"{i}_QBO_20_40.nc")) as ds:
            raw_data =ds.ucomp.sel(pfull=10,method='nearest')
            t = np.arange(len(raw_data.values))
            smoothed = rolling_average(raw_data,FIVE_MONTHS)
            mean,std,n,roots = get_qbo_period_transitions(smoothed,t)
            transition_indexs = np.round(roots).astype(int) 
            fourier_mean= get_qbo_period_fourier(smoothed)
            ampltiude_rmse = get_qbo_rmse_amplitude(smoothed)
            ampltiude_mean,amplitude_std = get_qbo_amplitude(raw_data.values,transition_indexs)

            qbo_periods[i] = mean
            qbo_periods_std[i] = std
            qbo_periods_fft[i] = fourier_mean
            qbo_count[i] = n
            qbo_amplitude_rmse[i] = ampltiude_rmse
            qbo_amplitude_mean[i] = ampltiude_mean
            qbo_amplitude_std[i] = amplitude_std


    df["qbo_periods"] = qbo_periods
    df["qbo_period_std"] = qbo_periods_std
    df["qbo_period_fft"] = qbo_periods_fft
    df["qbo_count"] = qbo_count
    df["qbo_rmse_ampltiude"] = qbo_amplitude_rmse
    df["qbo_amplitude_mean"] = qbo_amplitude_mean
    df["qbo_amplitude_std"] = qbo_amplitude_std

    df.to_csv(os.path.join(DATADIR,"qbo_data.csv"))


