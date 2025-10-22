import numpy as np
from scipy.fft import fft, fftfreq
from scipy.interpolate import InterpolatedUnivariateSpline


def rolling_average(signal: np.ndarray, n_months, points_per_month=1):
    N = n_months * points_per_month
    return np.convolve(signal, np.ones(N), mode="valid") / N


def get_signal_period_amplitude(
    signal: np.ndarray, smoothed_avg_months=5, points_per_month=1
):
    smoothed_signal = rolling_average(
        signal, n_months=smoothed_avg_months, points_per_month=points_per_month
    )
    transitions_ptv, transitions_neg = get_transitions(smoothed_signal)
    amplitudes = []
    for start, stop in zip(transitions_ptv[:-1], transitions_ptv[1:]):
        period_max = np.max(smoothed_signal[start:stop])
        period_min = np.min(smoothed_signal[start:stop])
        amplitudes.append((period_max - period_min) / 2)
    periods = np.array(transitions_ptv[1:] - transitions_ptv[:-1])
    return periods / points_per_month, np.array(amplitudes)


def get_transitions(signal: np.ndarray, offset=0):
    interp = InterpolatedUnivariateSpline(
        np.arange(offset, offset + len(signal)), signal
    )

    roots = interp.roots()
    derivatives_root = np.array([interp.derivatives(r)[1] for r in roots])

    transitions = np.round(roots).astype(int)  # round to nearest day
    return (
        transitions[derivatives_root >= 0],
        transitions[derivatives_root < 0],
    )


def get_period_fft(signal, points_per_month=1):
    signal = signal - np.mean(signal)  # Remove signal mean
    freqs = fftfreq(len(signal))
    signal_ft = fft(signal)
    imax_signal_ft = np.argmax(np.abs(signal_ft))
    return 1 / (points_per_month * freqs[imax_signal_ft])
