
'''Old Structured Document OCR - Main program'''
import cv2
import os
import json
import argparse
import pandas as pd
from aux_utils.page_tree import *
from aux_utils.image import *
from aux_utils.misc import *
from aux_utils import consts
from gui.osdocr_gui import run_gui
from ocr_box_module.ocr_box import *
from ocr_box_module.ocr_box_analyser import *
from ocr_box_module.ocr_box_fix import *
from ocr_engines.engine_utils import *
from output_module.journal.article import Article



def process_args():
    '''Process command line arguments'''
    parser = argparse.ArgumentParser(description='Old Structured Document OCR - Main program')
    parser.add_argument('--test'              ,action='store_true'                          ,help='Run tests')
    parser.add_argument('-g','--gui'          ,action='store_true'                          ,help='Run gui')
    parser.add_argument('-t','--target'       ,type=str,nargs=1                             ,help='Target image path')
    parser.add_argument('-f','--file'         ,type=str,nargs=1                             ,help='File that lists multiple target image paths. Assumed simple txt, with one path per line')
    parser.add_argument('-focr','--force_ocr' ,action='store_true',default=False            ,help='Force OCR engine to run again')
    args = parser.parse_args()
    return args


def run_test():
    '''Run tests'''
    target_image = consts.config['target_image_path']
    if target_image:
        # results path
        results_path = f'{consts.result_path}/{path_to_id(target_image)}'
        # get fixed results
        if os.path.exists(f'{results_path}/fixed/result_fixed.json'):
            ocr_results = OCR_Box(f'{results_path}/fixed/result_fixed.json')
        else:
            ocr_results = OCR_Box(f'{results_path}/result.json')
            ocr_results = bound_box_fix(ocr_results,2,None)
            ocr_results = categorize_boxes(ocr_results)
            ocr_results.id_boxes([2])
            result_dict_file = open(f'{results_path}/fixed/result_fixed.json','w')
            json.dump(ocr_results.to_json(),result_dict_file,indent=4)
            result_dict_file.close()
            image = draw_bounding_boxes(ocr_results,f'{results_path}/result.jpg',[2],id=True)
            cv2.imwrite(f'{results_path}/fixed/result_fixed.jpg',image)
            csv = pd.DataFrame(ocr_results.to_dict())
            csv.to_csv(f'{results_path}/fixed/result_fixed.csv')
        

        # get journal template
        image_info = get_image_info(f'{results_path}/fixed/result_fixed.jpg')
        journal_template = estimate_journal_template(ocr_results,image_info)
        columns_area = image_info
        columns_area.remove_box_area(journal_template['header'])
        columns_area.remove_box_area(journal_template['footer'])

        ocr_results = categorize_boxes(ocr_results)

        # run topologic_order
        # t_graph = topologic_graph(ocr_results,columns_area)
        # print('Topological graph: ')
        # t_graph.self_print()
        # order_list = sort_topologic_order(t_graph,ocr_results)
        # print('Order List: ',order_list)

        # run topologic_order context
        t_graph = topologic_order_context(ocr_results,columns_area)
        order_list = sort_topologic_order(t_graph,sort_weight=True)

        # change ids to order
        order_map = {order_list[i]:i for i in range(len(order_list))}
        ocr_results.change_ids(order_map)

        # draw reading order
        image = draw_bounding_boxes(ocr_results,f'{results_path}/fixed/result_fixed.jpg',[2],id=True)
        cv2.imwrite(f'{results_path}/reading_order.jpg',image)

        print('Order List: ',order_list)
        articles = graph_isolate_articles(t_graph)
        for article in articles:
            print('Article:',[b.id for b in article])
            
        with open(f'{results_path}/articles.txt','w') as f:
            for article in articles:
                article = Article(article)
                f.write(article.pretty_print())
                f.write('\n')

        with open(f'{results_path}/articles.md','w') as f:
            for article in articles:
                article = Article(article)
                f.write(article.to_md())
                f.write('\n'+'==='*40 + '\n')



def save_articles(articles,results_path):
    with open(f'{results_path}/articles.txt','w') as f:
        for article in articles:
            article = Article(article)
            f.write(article.pretty_print())
            f.write('\n')

    with open(f'{results_path}/articles.md','w') as f:
        for article in articles:
            article = Article(article)
            f.write(article.to_md())
            f.write('\n'+'==='*40 + '\n')


def run_target(target:str,force=False):
    '''Run pipeline for single target.
    
    1. OCR image
    2. Fix bounding boxes
    3. Categorize boxes
    5. Run topologic_order context
    6. Draw reading order
    7. Isolate articles
    
    TODO:
    1. Analyse image
    2. Image preprocessing
    3. Text post processing'''

    print(f'Processing: {target}')

    # check if target has been ocrd before
    results_path = f'{consts.result_path}/{path_to_id(target)}'
    print('Results path: ',results_path)
    if not force and os.path.exists(f'{results_path}/result.json'):
        print(f'Results exist: {target}')
    else:
        run_tesseract(target)

    # get results
    ocr_results = OCR_Box(f'{results_path}/result.json')

    ocr_results.id_boxes([2])

    # fix box bounds
    ocr_results = bound_box_fix(ocr_results,2,None)

    # categorize boxes
    ocr_results = categorize_boxes(ocr_results)

    # get journal template
    ## leaves only body
    image_info = get_image_info(target)
    journal_template = estimate_journal_template(ocr_results,image_info)
    columns_area = image_info
    columns_area.remove_box_area(journal_template['header'])
    columns_area.remove_box_area(journal_template['footer'])

    # run topologic_order context
    t_graph = topologic_order_context(ocr_results)

    # draw reading order
    image = draw_bounding_boxes(ocr_results,f'{results_path}/result.jpg',[2],id=True)
    cv2.imwrite(f'{results_path}/reading_order.jpg',image)

    # isolate articles
    articles = graph_isolate_articles(t_graph)

    # save articles
    save_articles(articles,results_path)









def run_main(args:argparse.Namespace):
    '''Run main program. Allows single image or multiple image list'''
    targets = []
    # single target
    if args.target:
        if os.path.exists(args.target[0]) or os.path.exists(f'{consts.current_path}/{args.target[0]}'):
            if os.path.exists(args.target[0]):
                targets.append(args.target[0])
            else:
                targets.append(f'{consts.current_path}/{args.target[0]}')
        else:
            raise FileNotFoundError(f'File not found: {args.target[0]}')
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
    else:
        print('No target specified. Please specify a target image or a target file.')
        sys.exit(0)

    if targets:
        for target in targets:
            run_target(target,args.force_ocr)



if __name__ == '__main__':
    read_configs()
    args = process_args()
    # test mode
    if args.test:
        run_test()

    # gui mode
    elif args.gui:
        run_gui()

    # normal mode
    else:
        run_main(args)




