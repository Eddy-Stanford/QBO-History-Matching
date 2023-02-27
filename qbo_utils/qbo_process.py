import numpy as np
from scipy.fft import fft, fftfreq
from scipy.interpolate import InterpolatedUnivariateSpline


def rolling_average(signal: np.ndarray, n_months, points_per_month=1):
    N = n_months * points_per_month
    return np.convolve(signal, np.ones(N), mode="same") / N


def get_signal_period_amplitude(
    signal: np.ndarray, smoothed_avg_months=5, points_per_month=1
):
    smoothed_signal = rolling_average(
        signal, n_months=smoothed_avg_months, points_per_month=points_per_month
    )
    interp = InterpolatedUnivariateSpline(np.arange(len(signal)), smoothed_signal, k=3)
    roots = interp.roots()
    transitions = np.round(roots).astype(int)
    amplitudes = []
    for (start, stop) in zip(transitions[::2], transitions[2::2]):
        period_max = np.max(signal[start:stop])
        period_min = np.min(signal[start:stop])
        amplitudes.append((period_max - period_min) / 2)
    periods = np.array(roots[2::2] - roots[:-2:2])
    return periods / points_per_month, np.array(amplitudes)


def get_period_fft(signal, points_per_month=1):
    signal = signal - np.mean(signal)  # Remove signal mean
    freqs = fftfreq(len(signal))
    signal_ft = fft(signal)
    imax_signal_ft = np.argmax(np.abs(signal_ft))
    return 1 / (points_per_month * freqs[imax_signal_ft])
