
'''Old Structured Document OCR - Main program'''
import argparse
import os
import sys
from parse_args import process_args
from aux_utils.misc import *
from aux_utils import consts
from gui.osdocr_gui import run_gui
from ocr_tree_module.ocr_tree import *
from preprocessing.image import *
from pipeline import run_target
from ocr_tree_module.ocr_tree_analyser import *
from validation.calibrate import run_calibrate





def run_test():
    '''Run tests'''
    target_image = consts.config['target_image_path']
    print('test','target_image',target_image)
    if target_image:
        # test unite blocks
        # ocr_results_path = f'{consts.result_path}/{path_to_id(target_image)}/processed/ocr_results.json'
        # ocr_results = OCR_Tree(ocr_results_path)
        # # Frequency tests
        # get_text_sizes(ocr_results,method='savgol_filter',logs=True)
        # get_text_sizes(ocr_results,method='WhittakerSmoother',logs=True)
        #get_columns(ocr_results,method='savgol_filter',logs=True)
        # get_columns(ocr_results,method='WhittakerSmoother',logs=True)
        # get_columns_pixels(target_image,method='WhittakerSmoother',logs=True)
        #get_journal_areas(ocr_results,logs=True)
        # Waifu2x test
        result_image_path = f'{consts.result_path}/result_waifu2x.png'
        
        # run_waifu2x(target_image,result_image_path=result_image_path,method='noise',noise_level=3,logs=True)
        # run_waifu2x(target_image,result_image_path=result_image_path,method='noise',noise_level=3,logs=True)
        run_waifu2x(target_image,result_image_path=result_image_path,method='autoscale',noise_level=-1,logs=True)

        # detectron2 test
        # test_detectron2(target_image)

        # layout parser test
        # remove_document_images(target_image,logs=True)


   




def run_main(args:argparse.Namespace):
    '''Run main program. Allows single image or multiple image list'''

    targets = []

    # single target
    if args.target:
        # check if targets exist
        for target in args.target:
            if os.path.exists(target) or os.path.exists(f'{consts.current_path}/{target}'):
                if os.path.exists(target):
                    targets.append(target)
                else:
                    targets.append(f'{consts.current_path}/{target}')
            else:
                print(f'File not found: {target}')
                sys.exit(0)

    # multiple targets
    ## process file
    elif args.file:
        if os.path.exists(args.file[0]) or os.path.exists(f'{consts.current_path}/{args.file[0]}'):
            file = None
            if os.path.exists(args.file[0]):
                file = args.file[0]
            else:
                file = f'{consts.current_path}/{args.file[0]}'

            with open(file) as f:
                for line in f:
                    target = line.strip()
                    if os.path.exists(target):
                        targets.append(target)
                    else:
                        print(f'File not found: {target}')
        else:
            raise FileNotFoundError(f'File not found: {args.file[0]} or {consts.current_path}/{args.file[0]}')
        
    # config target
    elif os.path.exists(consts.config['target_image_path']):
        targets.append(consts.config['target_image_path'])

    else:
        print('No target specified. Please specify a target image or a target file.')
        sys.exit(0)

    # run targets
    if targets:
        for target in targets:
            if args.calibrate:
                run_calibrate(args.calibrate[0],args.calibrate[1],args.calibrate_no_reuse == False,args.logs,args.debug)
            else:
                run_target(target,args)





if __name__ == '__main__':
    print('''
        =============================
        =============================
        ||          OSDOCR         ||
        =============================
        =============================
          ''')
    read_configs()
    args = process_args()

    # create tmp folder
    if not os.path.exists(consts.tmp_path):
        os.makedirs(consts.tmp_path)

    # change result path
    if args.output_folder:
        consts.result_path = args.output_folder

    # test mode
    if args.test:
        run_test()

    # gui mode
    elif args.gui:
        run_gui()

    # normal mode
    else:
        run_main(args)
        

    # clean tmp folder files
    clean_tmp_folder()




