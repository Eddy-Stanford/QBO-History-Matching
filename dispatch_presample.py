import dispatch_utils
import argparse
import pandas as pd 

parser = argparse.ArgumentParser(description="Dispatch MiMA runs for a known set of parameters")
parser.add_argument("parameters",type=str,help='CSV file containing parameters to sample over')
parser.add_argument("n_years",type=dispatch_utils.positive_int,default=40)
parser.add_argument("--exp-name",default=None,type=str)

if __name__ == '__main__':
    args = parser.parse_args()
    base = dispatch_utils.get_base_dir(args.exp_name)
    template = dispatch_utils.get_template()
    samples:pd.DataFrame = pd.read_csv(args.parameters)
    for run,series in samples.iterrows():
        run_dir = dispatch_utils.create_run_dirs(base,run)
        dispatch_utils.write_namefile(run_dir,template,**series.to_dict())
    dispatch_utils.model_run(base,len(samples),args.n_years)

