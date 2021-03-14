import argparse
import sys

from spleeter.separator import Separator


def main(args):
    parser = argparse.ArgumentParser(description="Do something.")
    parser.add_argument("-input_path", "--input_path", type=str, default='', required=True)
    parser.add_argument("-output_directory", "--output_directory", type=str, default='', required=True)
    separator = Separator('spleeter:2stems')
    args = parser.parse_args(args)
    separator.separate_to_file(args.input_path, args.output_directory)


if __name__ == '__main__':
    main(sys.argv[1:])
