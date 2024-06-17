'''Validation command script'''

import argparse
import json
import os
import sys
import shutil

from OSDOCR.validation.calibrate import run_calibrate

run_path = os.getcwd()

def process_args()->argparse.Namespace:
    parser = argparse.ArgumentParser(description='OSDOCR - Validation')
    parser.add_argument('validation_folder',                        type=str, nargs=1,                                          help='''Folder with validation files. 
                        Validation files:
                            * target_image.* (extension should of image format) !
                            * ground_truth.txt                                  !
                            * partial_ground_truth.txt                          !
                            * expected_results.json
                        
                            ! - required (in the case of ground_truth.txt and partial_ground_truth.txt only one is required, but both are useful)''')
    parser.add_argument('-pc','--pipeline_config',                  type=str, nargs='+',                                        help='pipeline config(s) to use and compare. JSON format. Can be given a list of configs which will be compared, a single config will be used for all or a directory of configs.')
    parser.add_argument('-rr', '--reuse_results',                    action='store_true',                                       help='Reuse results from previous runs.')
    parser.add_argument('-o', '--output',                           type=str, nargs=1, default=[f'{run_path}/clean_ocr.json'],  help='output path for cleaned ocr results')
    parser.add_argument('-l', '--logs',                                         action='store_true',                            help='Print logs')
    parser.add_argument('-d', '--debug',                                        action='store_true',                            help='Debug mode')


    args = parser.parse_args()
    return args



def main():

    args = process_args()

    output_path = args.output[0]

    # check if output path exists
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)

    calibration_folder = args.validation_folder[0] if args.validation_folder else os.getcwd()
    # check if calibration folder exists
    if not os.path.exists(calibration_folder):
        print(f'Calibration folder not found: {calibration_folder}')
        sys.exit(0)


    # check format of pipeline config
    pipeline_config = None
    if args.pipeline_config:
        if len(args.pipeline_config) == 1:
            if not os.path.exists(args.pipeline_config[0]):
                print(f'Pipeline config not found: {args.pipeline_config[0]}')
                sys.exit(0)

            # directory
            ## save json files
            if os.path.isdir(args.pipeline_config[0]):
                pipeline_config = []
                files = os.listdir(args.pipeline_config[0])
                for file in files:
                    if file.endswith('.json'):
                        pipeline_config.append(f'{args.pipeline_config[0]}/{file}')
            # single config
            else:
                if not args.pipeline_config[0].endswith('.json'):
                    print(f'Pipeline config format not supported: {args.pipeline_config[0]}')
                    sys.exit(0)
                pipeline_config = args.pipeline_config[0]
        # multiple configs
        elif len(args.pipeline_config) > 1:
            pipeline_config = []
            # save valid json files
            for config in args.pipeline_config:
                if os.path.exists(config) and config.endswith('.json'):
                    pipeline_config.append(config)

    if pipeline_config:
        # tmp dir
        tmp_dir = f'{run_path}/tmp'
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir, exist_ok=True)

        # copy all config files to tmp dir
        for config in pipeline_config:
            shutil.copy(config, tmp_dir)

        # run calibration
        run_calibrate(calibration_folder, tmp_dir, args.reuse_results, args.logs, args.debug)

        # print result of each config
        if args.logs:
            for config in pipeline_config:
                config_basename = os.path.basename(config)
                config_results = f'{calibration_folder}/results/{config_basename}/results.json'
                if os.path.exists(config_results):
                    with open(config_results, 'r') as f:
                        results = json.load(f)
                        print(f'{config_basename} - score: {results["score"]}')
                else:
                    print(f'{config_basename} - score: -')

        # clean tmp dir
        shutil.rmtree(tmp_dir)

    
        
    


