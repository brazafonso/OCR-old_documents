'''OCR to simple format command script'''

import argparse
import json
import os
import sys

from OSDOCR.ocr_tree_module.ocr_tree import OCR_Tree
from OSDOCR.ocr_tree_module.ocr_tree_analyser import extract_articles, order_ocr_tree
from OSDOCR.output_module.journal.article import Article

run_path = os.getcwd()

def process_args()->argparse.Namespace:
    parser = argparse.ArgumentParser(description='OSDOCR - OCR to Simple Format')
    parser.add_argument('ocr_results',                              type=str, nargs=1,                                          help='target ocr results to clean')
    parser.add_argument('-t', '--target',                           type=str, nargs=1,                                          help='target image')
    parser.add_argument('-ot', '--output_type',                     type=str, nargs=1, default=['md'],                          help='output type. Options: txt, md. Default: md',choices=['txt','txt_simple','md'])
    parser.add_argument('-tcro','--toggle_calculate_reading_order', action='store_false',                                       help='Toggle calculate reading order in ocr results (default: True).')
    parser.add_argument('-id','--ignore_delimiters',                action='store_true',                                        help='ignore delimiters when calculating reading order.')
    parser.add_argument('-tc', '--text_confidence',                 type=int, nargs=1, default=[10],                            help='text confidence for ocr result filtering.')
    parser.add_argument('-o', '--output',                           type=str, nargs=1, default=[],                              help='output path for cleaned ocr results')
    parser.add_argument('-l', '--logs',                                         action='store_true',                            help='Print logs')
    parser.add_argument('-d', '--debug',                                        action='store_true',                            help='Debug mode')


    args = parser.parse_args()
    return args


def save_output(blocks:list[OCR_Tree],output_path:str,output_type:str,min_text_conf:int,logs:bool=False):
    '''Save articles to output path'''

    if 'md' in output_type:
        output_stream = open(f'{output_path}/output.md','w',encoding='utf-8') if output_path else sys.stdout
        for block in blocks:
            block_txt = block.to_text(min_text_conf)
            output_stream.write(block_txt)


    if 'html' in output_type:
        # TODO
        pass


    if 'txt' in output_type:
        output_stream = open(f'{output_path}/output.txt','w',encoding='utf-8') if output_path else sys.stdout
        for block in blocks:
            block_txt = block.to_text(min_text_conf)
            output_stream.write(block_txt)


    if 'txt_simple' in output_type:
       # TODO
       pass



def main():

    args = process_args()

    ocr_results = OCR_Tree(args.ocr_results[0])
    target_path = args.target[0] if args.target else None

    if not os.path.exists(target_path):
        print(f'Target path not found: {target_path}')
        sys.exit(0)

    output_path = args.output[0] if args.output else None

    # check if output path exists
    if output_path and not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)

    calculate_reading_order_flag = args.toggle_calculate_reading_order

    # get blocks of text
    if calculate_reading_order_flag:
        # calculate reading order
        blocks = order_ocr_tree(target_path,ocr_results,args.ignore_delimiters,args.logs)
    else:
        # natural OCR order
        blocks = [block for block in ocr_results.get_boxes_level(2,ignore_type=[] if not args.ignore_delimiters else ['delimiter'])]
        blocks = sorted(blocks,key=lambda x: x.id)

    
    # create output
    save_output(blocks,output_path,args.output_type[0],args.text_confidence[0],args.logs)
    


