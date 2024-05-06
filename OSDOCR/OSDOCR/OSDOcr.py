
'''Old Structured Document OCR - Main program'''
import os
import argparse
import sys
from aux_utils.parse_args import *
from aux_utils.misc import *
from aux_utils import consts
from gui.osdocr_gui import run_gui
from ocr_tree_module.ocr_tree import *
from preprocessing.image import *
from pipeline import run_target
from ocr_tree_module.ocr_tree_analyser import *



skipable_methods = ['clean_ocr','unite_blocks','auto_rotate','fix_distortions',
                    'noise_removal','blur_removal','lightning_correction',
                    'image_upscaling','extract_articles','image_preprocess']





def process_args():
    '''Process command line arguments'''
    parser = argparse.ArgumentParser(description='''
--------------------------------------------------------------
|        Old Structured Document OCR - Main program          |
--------------------------------------------------------------
            
Components:
            - INPUT:
            * Image 
            * hOCR
            
            - PIPELINE:
            * A : Image input
                ^ TODO
            * B : hOCR input
                ^ TODO
            
            - OUTPUT:
            * Markdown
            * HTML
            * TXT
                                     
                                     ''',formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--test'                     ,action='store_true'                                           ,help='Run tests')
    parser.add_argument('-g','--gui'                 ,action='store_true'                                           ,help='Run gui')
    parser.add_argument('target'                     ,type=str,nargs='*'                                            ,help='Target image path')
    parser.add_argument('-f','--file'                ,type=str,nargs=1                                              ,help='File that lists multiple target image paths. Assumed simple txt, with one path per line')
    parser.add_argument('-of','--output_folder'      ,type=str,nargs=1                                              ,help='Results folder')
    parser.add_argument('-ot','--output_type'        ,type=str,nargs='*' ,default=['markdown']                      ,help='Output type. Possible values: markdown, html, txt (default: markdown).')
    parser.add_argument('-focr','--force_ocr'        ,action='store_true',default=False                             ,help='Force OCR engine to run again')
    parser.add_argument('-id','--ignore_delimiters'  ,action='store_true',default=False                             ,help='Ignore delimiters as page/column boundaries (default: False)')
    parser.add_argument('-fr','--fix_rotation'       ,type=str,nargs='?' ,default=['auto'],const='auto'             ,help='Fix image rotation automatically (default: True). Further options: auto, clockwise, counter_clockwise (default: auto).')
    parser.add_argument('-upi','--upscaling_image'   ,type=str,nargs='*' ,default=['waifu2x']                       ,help='''
Upscale image automatically (default: waifu2x). 
Further options: 
    - waifu2x
            * scale2x
            * scale4x
                        ''',action=CustomAction_upscale_image)
    parser.add_argument('-di','--denoise_image'   ,type=str,nargs='*' ,default=['waifu2x']                          ,help='''
Upscale image automatically (default: waifu2x). 
Further options: 
    - waifu2x
            * [-1,0,1,2,3]
                        ''',action=CustomAction_denoise_image)
    parser.add_argument('--tesseract_config'         ,type=str,nargs='*' ,default=['__l','por']                  ,help='Tesseract config. Check tesseract --help-extra for more info. Seperate flags with "__"',action=CustomAction_tesseract_config)
    parser.add_argument('--skip_method'              ,type=str,nargs='*',default=[]                                 ,help='Skip method on target. Possible values: ' + ', '.join(skipable_methods))
    parser.add_argument('-d','--debug'               ,action='store_true',default=False                             ,help='Debug mode')
    args = parser.parse_args()
    return args


def clean_tmp_folder():
    '''Clean tmp folder. Removes all files in tmp folder with 'OSDOcr' in the name''' 
    if os.path.exists(consts.tmp_path):
        files = os.listdir(consts.tmp_path)
        for file in files:
            if 'OSDOcr' in file:
                os.remove(f'{consts.tmp_path}/{file}')


def run_test():
    '''Run tests'''
    target_image = consts.config['target_image_path']
    print('test','target_image',target_image)
    if target_image:
        # test unite blocks
        # ocr_results_path = f'{consts.result_path}/{path_to_id(target_image)}/result.json'
        # ocr_results = OCR_Tree(ocr_results_path)
        # # Frequency tests
        # get_text_sizes(ocr_results,method='savgol_filter',log=True)
        # get_text_sizes(ocr_results,method='WhittakerSmoother',log=True)
        #get_columns(ocr_results,method='savgol_filter',log=True)
        # get_columns(ocr_results,method='WhittakerSmoother',log=True)
        # get_columns_pixels(target_image,method='WhittakerSmoother',log=True)
        #get_journal_areas(ocr_results,log=True)

        # Waifu2x test
        # result_image_path = f'{consts.result_path}/result_waifu2x.png'
        # run_waifu2x(target_image,result_image_path=result_image_path,method='noise',noise_level=3,log=True)
        # run_waifu2x(target_image,result_image_path=result_image_path,method='noise',noise_level=3,log=True)
        # run_waifu2x(target_image,result_image_path=result_image_path,method='scale4x',noise_level=3,log=True)

        # detectron2 test
        # test_detectron2(target_image)

        # layout parser test
        remove_document_images(target_image,logs=True)


   




def run_main(args:argparse.Namespace):
    '''Run main program. Allows single image or multiple image list'''

    if args.debug:
        print(f'''
        ---------------------------
        |      Running OSDOCR     |
        ---------------------------
              ''')

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




