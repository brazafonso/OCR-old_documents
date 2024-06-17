'''OCR to articles command script'''

import argparse
import json
import os
import sys

from OSDOCR.ocr_tree_module.ocr_tree import OCR_Tree
from OSDOCR.ocr_tree_module.ocr_tree_analyser import extract_articles
from OSDOCR.output_module.journal.article import Article

run_path = os.getcwd()

def process_args()->argparse.Namespace:
    parser = argparse.ArgumentParser(description='OSDOCR - OCR to Articles')
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


def save_articles(articles:list[OCR_Tree],output_path:str,output_type:str,min_text_conf:int,logs:bool=False):
    '''Save articles to output path'''

    if 'md' in output_type:
        output_stream = open(f'{output_path}/articles.md','w',encoding='utf-8') if output_path else sys.stdout
        for article in articles:
            article = Article(article,min_text_conf)
            output_stream.write(article.to_md())
            output_stream.write('\n'+'==='*40 + '\n')


    if 'html' in output_type:
        # TODO
        pass


    if 'txt' in output_type:
        # TODO
        pass


    if 'txt_simple' in output_type:
        output_stream = open(f'{output_path}/articles.txt','w',encoding='utf-8') if output_path else sys.stdout
        for article in articles:
            article = Article(article,min_text_conf)
            output_stream.write(article.to_txt())



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

    # get articles and order
    _, articles = extract_articles(image_path=target_path,
                                             ocr_results=ocr_results, 
                                             ignore_delimiters=args.ignore_delimiters, 
                                             calculate_reading_order=args.toggle_calculate_reading_order, 
                                             logs=args.logs)
    
    # create output
    save_articles(articles,output_path,args.output_type,args.text_confidence[0],args.logs)
    


