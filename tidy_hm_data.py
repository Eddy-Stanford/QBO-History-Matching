#!/usr/bin/env python3
"""
Tidy up history matching, create single CSV file with all wave relevant information merged into one place
Consistent with EKI file format, allows direct comparison between methods
"""
if __name__ == "__main__":
    import argparse
    import os
    import re
    import sys
    from glob import glob

    import numpy as np
    import pandas as pd

    parser = argparse.ArgumentParser(
        description=(
            "Tidy up history matching, create single CSV file with all wave relevant information merged into one place\n"
            "Consistent with EKI file format, allows direct comparison between methods"
        )
    )
    parser.add_argument(
        "input_dir", help="Input directory of history matching experiment"
    )

    args = parser.parse_args()

    base_files = sorted(
        glob(os.path.join(args.input_dir, "*_samples.csv")),
        key=lambda x: int(re.search(r"\d+(?=_samples.csv)", x).group()),
    )
    ## TODO: make i f
    for i, base in enumerate(base_files):
        df = pd.read_csv(base, index_col="run_id")

        analysis_directory = os.path.join(args.input_dir, f"wave_{i}", "analysis")
        try:
            output = np.load(os.path.join(analysis_directory, "y.npy"))
            output_err = np.load(os.path.join(analysis_directory, "y_err.npy"))
        except FileNotFoundError:
            print(f"[WARN] No output data for {i} - skipping", file=sys.stderr)
            continue
        df[["period", "amplitude"]] = output
        df[["period_sem", "amplitude_sem"]] = output_err

        df.to_csv(os.path.join(os.path.dirname(base), f"output_{i}.csv"))
        print(f"[INFO] Done wave {i}")
    print("[DONE] All done ")
