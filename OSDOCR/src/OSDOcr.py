
'''Old Structured Document OCR - Main program'''
import cv2
import os
import json
import argparse
import pandas as pd
from aux_utils.page_tree import *
from document_image_utils.image import *
from aux_utils.misc import *
from aux_utils import consts
from gui.osdocr_gui import run_gui
from ocr_tree_module.ocr_tree import *
from ocr_tree_module.ocr_tree_analyser import *
from ocr_tree_module.ocr_tree_fix import *
from ocr_engines.engine_utils import *
from output_module.journal.article import Article


skipable_methods = ['clean_ocr','unite_blocks','auto_rotate','fix_distortions',
                    'noise_removal','blur_removal','lightning_correction',
                    'image_upscaling','extract_articles']


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
    parser.add_argument('--test'                     ,action='store_true'                               ,help='Run tests')
    parser.add_argument('-g','--gui'                 ,action='store_true'                               ,help='Run gui')
    parser.add_argument('target'                     ,type=str,nargs='*'                                ,help='Target image path')
    parser.add_argument('-f','--file'                ,type=str,nargs=1                                  ,help='File that lists multiple target image paths. Assumed simple txt, with one path per line')
    parser.add_argument('-of','--output_folder'      ,type=str,nargs=1                                  ,help='Results folder')
    parser.add_argument('-ot','--output_type'        ,type=str,nargs='*' ,default=['markdown']          ,help='Output type. Possible values: markdown, html, txt (default: markdown).')
    parser.add_argument('-focr','--force_ocr'        ,action='store_true',default=False                 ,help='Force OCR engine to run again')
    parser.add_argument('-id','--ignore_delimiters'  ,action='store_true',default=False                 ,help='Ignore delimiters as page/column boundaries (default: False)')
    parser.add_argument('-fr','--fix_rotation'       ,type=str,nargs='?' ,default=None,const='auto'     ,help='Fix image rotation automatically (default: False). Further options: auto, clockwise, counter_clockwise (default: auto).')
    parser.add_argument('--skip_method'              ,type=str,nargs='*',default=[]                     ,help='Skip method on target. Possible values: ' + ', '.join(skipable_methods))
    parser.add_argument('-d','--debug'               ,action='store_true',default=False                 ,help='Debug mode')
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
        ocr_results_path = f'{consts.result_path}/{path_to_id(target_image)}/result.json'
        ocr_results = OCR_Tree(ocr_results_path)
        ocr_results.id_boxes([2])
        ocr_results = categorize_boxes(ocr_results)
        ocr_results = unite_blocks(ocr_results)
        results_path = f'{consts.result_path}/{path_to_id(target_image)}/fixed/united.json'
        json_format = ocr_results.to_json()
        with open(results_path,'w') as f:
            json.dump(json_format,f,indent=4)


def save_articles(articles:list,results_path:str,args:argparse.Namespace):
    '''Save articles. Type of output is defined in args : markdown, html, txt'''
    output_types = args.output_type

    if 'markdown' in output_types:
        with open(f'{results_path}/articles.txt','w',encoding='utf-8') as f:
            for article in articles:
                article = Article(article)
                f.write(article.pretty_print())
                f.write('\n')

        with open(f'{results_path}/articles.md','w',encoding='utf-8') as f:
            for article in articles:
                article = Article(article)
                f.write(article.to_md())
                f.write('\n'+'==='*40 + '\n')

    if 'html' in output_types:
        # TODO
        pass

    if 'txt' in output_types:
        # TODO
        pass

def extract_articles(target:str,ocr_results:OCR_Tree,results_path:str,args:argparse.Namespace):
    '''Extract articles from image'''

    # get journal template
    ## leaves only body
    image_info = get_image_info(target)
    journal_template = estimate_journal_template(ocr_results,image_info)
    columns_area = image_info
    columns_area.remove_box_area(journal_template['header'])
    columns_area.remove_box_area(journal_template['footer'])

    # run topologic_order context
    t_graph = topologic_order_context(ocr_results,area=columns_area,ignore_delimiters=args.ignore_delimiters)
    order_list = sort_topologic_order(t_graph,sort_weight=True)


    # isolate articles
    articles = graph_isolate_articles(t_graph,order_list=order_list)
    if args.debug:
        articles_img = draw_articles(articles,target)
        cv2.imwrite(f'{results_path}/articles.png',articles_img)

    # draw reading order
    if args.debug:
        # change ids to order
        order_map = {order_list[i]:i for i in range(len(order_list))}
        ocr_results.change_ids(order_map)

        image = draw_bounding_boxes(ocr_results,target,[2],id=True)
        cv2.imwrite(f'{results_path}/reading_order.png',image)


    # save articles
    save_articles(articles,results_path,args)


    


def image_preprocess(target:str,args:argparse.Namespace):
    '''Preprocess image'''
    if args.debug:
        print('IMAGE PREPROCESS')
    tmp_image_path = f'{consts.tmp_path}/OSDOcr_image_tmp.png'

    # save image
    og_img = cv2.imread(target)
    cv2.imwrite(tmp_image_path,og_img)

    # image rotation
    ## not used by default
    if args.fix_rotation and 'auto_rotate' not in args.skip_method:
        rotate_img = rotate_image(target,direction=args.fix_rotation,debug=args.debug)
        cv2.imwrite(tmp_image_path,rotate_img)

    # image distortion
    if 'fix_distortions' not in args.skip_method:
        # TODO
        pass

    # noise removal
    if 'noise_removal' not in args.skip_method:
        # TODO
        pass

    # blur removal
    if 'blur_removal' not in args.skip_method:
        # TODO
        pass

    # image upscaling
    if 'image_upscaling' not in args.skip_method:
        # TODO
        pass

    # lightning correction
    if 'lightning_correction' not in args.skip_method:
        # TODO
        pass

    return tmp_image_path


def run_target_hocr(target:str,args:argparse.Namespace):
    '''Run pipeline for single OCR target. TODO'''
    return None


def run_target_image(target:str,results_path:str,args:argparse.Namespace):
    '''Run pipeline for single image.
    - Image preprocessing
    - OCR
    - Convert to ocr_tree
    '''
    
    # preprocess image
    target = image_preprocess(target,args)
            
    run_tesseract(target,results_path=results_path)

    # get results
    return OCR_Tree(f'{results_path}/result.json')


def run_target(target:str,args:argparse.Namespace):
    '''Run pipeline for single target.
    
    - A : image
    1. Analyze target 
    2. Preprocess image
    3. OCR
    4. Convert to ocr_tree


    - B : hOCR
    1. Convert to ocr_tree

    - General
    1. Clean ocr_tree
    2. Analyse ocr_tree
    3. Extract articles
    4. Save articles

    '''
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    if args.debug:
        print(f'Processing: {target}')

    image_target = True
    # check if target is hOCR
    if target.endswith('.hocr'):
        image_target = False

    ocr_results = None

    if not image_target:
        ocr_results = run_target_hocr(target,args)
    else:
        force_ocr = args.force_ocr
        # check if target has been ocrd before or force
        if force_ocr or not os.path.exists(f'{consts.result_path}/{path_to_id(target)}/result.json'):
            ocr_results = run_target_image(target,results_path,args)
        else:
            if os.path.exists(f'{consts.result_path}/{path_to_id(target)}/result.json'):
                ocr_results = OCR_Tree(f'{consts.result_path}/{path_to_id(target)}/result.json')
            else:
                print('File not found: ',f'{consts.result_path}/{path_to_id(target)}/result.json')
                print('Please run ocr first')
                sys.exit(1)

    # id boxes
    ocr_results.id_boxes([2])

    if args.debug:
        id_img = draw_bounding_boxes(ocr_results,target,[2],id=True)
        cv2.imwrite(f'{results_path}/result_id_0.png',id_img)

    # clean ocr_results
    if 'clean_ocr' not in args.skip_method:
        ocr_results = bound_box_fix(ocr_results,2,None)

    # categorize boxes
    ocr_results = categorize_boxes(ocr_results)

    # unite same type blocks
    if 'unite_blocks' not in args.skip_method:
        ocr_results = unite_blocks(ocr_results)

    if args.debug:
        id_img = draw_bounding_boxes(ocr_results,target,[2],id=True)
        cv2.imwrite(f'{results_path}/result_id_2.png',id_img)

    if args.debug:
        # analyse ocr_results
        results = analyze_text(ocr_results)
        print(results)

    # extract articles
    if 'extract_articles' not in args.skip_method:
        extract_articles(target,ocr_results,results_path,args)

   









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
            run_target(target,args)





if __name__ == '__main__':
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




