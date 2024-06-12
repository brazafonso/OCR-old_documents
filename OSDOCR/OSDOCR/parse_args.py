import argparse
from aux_utils.parse_args import *
from aux_utils import consts


preprocessing_methods = ['auto_rotate','noise_removal','blur_removal','lightning_correction',
                         'image_preprocess','cut_document_margins','remove_document_images',
                         'image_upscaling']

posprocessing_methods = ['clean_ocr','unite_blocks','calculate_reading_order','extract_articles']

skipable_methods = ['all'] + preprocessing_methods + posprocessing_methods

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
            * TXT Simple
                                     
                                     ''',formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--test'                        ,action='store_true'                                           ,help='Run tests')
    parser.add_argument('-g','--gui'                    ,action='store_true'                                           ,help='Run gui')
    parser.add_argument('target'                        ,type=str,nargs='*'                                            ,help='Target image path')
    parser.add_argument('-sgocr','--segmented_ocr'      ,action='store_true'                                           ,help='Segment target and apply OCR in each segment, merging results into single tree (default: False).')
    parser.add_argument('-f','--file'                   ,type=str,nargs=1                                              ,help='File that lists multiple target image paths. Assumed simple txt, with one path per line')
    parser.add_argument('-of','--output_folder'         ,type=str,nargs=1                                              ,help='Results folder')
    parser.add_argument('-ot','--output_type'           ,type=str,nargs='*' ,default=['markdown']                      ,help='Output type. Possible values: markdown, html, txt (default: markdown).', choices=['markdown','html','txt','txt_simple'])
    parser.add_argument('-tc','--text_confidence'       ,type=int,nargs=1   ,default=10                                ,help='Text confidence level. Possible values: 0-100.')
    parser.add_argument('-tt','--target_type'           ,type=str,nargs=1   ,default='newspaper'                       ,help='Target type. Possible values: newspaper.')
    parser.add_argument('-tod','--target_old_document'  ,action='store_false',default=True                             ,help='Target is an old document (default: True). Used for automatic pipeline decisions, ex.: choosing model to identify document images.')
    parser.add_argument('-focr','--force_ocr'           ,action='store_true',default=False                             ,help='Force OCR engine to run again')
    parser.add_argument('-id','--ignore_delimiters'     ,action='store_true',default=False                             ,help='Ignore delimiters as page/column boundaries (default: False)')
    parser.add_argument('-fr','--fix_rotation'          ,type=str,nargs='?' ,default=['auto'],const='auto'             ,help='Fix image rotation automatically (default: True). Further options: auto, clockwise, counter_clockwise (default: auto).',choices=['auto','clockwise','counter_clockwise'])
    parser.add_argument('-upi','--upscaling_image'      ,type=str,nargs='*' ,default=['waifu2x']                       ,help='''
Upscale image automatically (default: waifu2x). 
Further options: 
    - waifu2x
            * scale2x
            * scale4x
            * autoscale
                        ''',action=CustomAction_upscale_image)
    parser.add_argument('-tdpi','--target_dpi'          ,type=int,nargs='?' ,default=300                            ,help='Target dpi for image (default: 300)')
    parser.add_argument('-tdim','--target_dimensions'   ,type=str,nargs='?' ,default='A3'                           ,help='''
Real page dimensions for image (default: A3). 
Used to calculate image dpi.
Available formats ('/OSDOCR/consts/dimensions.json' , more can be added):
    - A5
    - A4
    - A3
    - A2
    - A1
    - 2A0
                        ''',choices=consts.config['dimensions'].keys())
    parser.add_argument('-di','--denoise_image'         ,type=str,nargs='*' ,default=['waifu2x']                        ,help='''
Upscale image automatically (default: waifu2x). 
Further options: 
    - waifu2x
            * [-1,0,1,2,3]
                        ''',action=CustomAction_denoise_image)
    parser.add_argument('-rdi','--remove_document_images',type=str,nargs='*' ,default=['leptonica']                     ,help='Identify document images automatically (default: leptonica).',choices=['leptonica','layoutparser'])
    t = parser.add_argument('--tesseract_config'     ,type=str,nargs='*'    ,default=['__l','por']                      ,help='Tesseract config. Check tesseract --help-extra for more info. Seperate flags with "__"',action=CustomAction_tesseract_config)
    parser.add_argument('--skip_method'              ,type=str,nargs='*'    ,default=[]                                 ,help='Skip method on target. Possible values: ' + ', '.join(skipable_methods),action=CustomAction_skip_method,choices=skipable_methods)
    parser.add_argument('--calibrate'                ,type=str,nargs='+'                                                ,help='Calibrate pipeline by using specifying a folder with a target and results for comparison. A folder for pipeline configs can also be given. By default, uses pipeline config folder in validation folder.',action=CustomAction_calibrate)
    parser.add_argument('--calibrate_no_reuse',       action='store_true',default=False                                 ,help='Do not reuse results of previous calibration runs.')
    parser.add_argument('-pc','--pipeline_config'    ,type=str,nargs=1                                                  ,help='Pipeline config file.',action=CustomAction_pipeline_config)
    parser.add_argument('-l','--logs'                ,action='store_false'  ,default=True                               ,help='Print logs')
    parser.add_argument('-d','--debug'               ,action='store_true'   ,default=False                              ,help='Debug mode')
    



    ns = argparse.Namespace()
    args = parser.parse_args(namespace=ns)

    # run action even with default
    t(parser,ns,t.default,'tesseract_config')

    return args