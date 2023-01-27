import numpy as np
import argparse
import os
import csv
from pyDOE import lhs
import dispatch_utils

parser = argparse.ArgumentParser(description='Run Uncertanity Quantification experiments')
parser.add_argument('n_years',default=20,type=dispatch_utils.positive_int)
parser.add_argument('n_runs',default=20,type=dispatch_utils.positive_int)
parser.add_argument('--seed',default=None,type=int)
parser.add_argument('--rng-offset',default=0,type=int)
parser.add_argument('--exp-name',default=None,type=str)

if __name__ == '__main__':
    args = parser.parse_args()
    base = dispatch_utils.get_base_dir(args.exp_name)
    template = dispatch_utils.get_template()
    samples = lhs(2,samples=args.n_runs) 
    samples = np.column_stack((samples,np.ones((args.n_runs,))))
    rescale = np.array([[60,0],[0,0.005],[5,0.001]])
    samples = (samples @ rescale)

    for run in range(args.n_runs):
        run_cw = samples[run,0]
        run_Bt = samples[run,1]
        run_dir = dispatch_utils.create_run_dirs(base,run)
        dispatch_utils.write_namefile(run_dir,template,run_cw,run_Bt)
    
    
    with open(os.path.join(base,'paramlist.csv'),'w',newline='\n') as f:
        paramlist = csv.writer(f, delimiter=',',
                        quotechar='|', quoting=csv.QUOTE_MINIMAL)
        paramlist.writerow(['run_id','cw','Bt'])
        paramlist.writerows([[i,str(samples[i,0]),str(samples[i,1])] for i in range(args.n_runs)])

    dispatch_utils.model_run()