import argparse
import dispatch_utils

parser = argparse.ArgumentParser(description='')
parser.add_argument('configfile',type=str)
parser.add_argument('waveno',type=dispatch_utils.positive_int)

if __name__ == '__main__':


