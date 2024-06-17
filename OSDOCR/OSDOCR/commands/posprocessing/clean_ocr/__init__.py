'''Clean OCR command script'''

import argparse
import json
import os
from OSDOCR.ocr_tree_module.ocr_tree import OCR_Tree
from OSDOCR.ocr_tree_module.ocr_tree_fix import bound_box_fix, unite_blocks
from OSDOCR.preprocessing.image import identify_document_images
from document_image_utils.image import get_document_delimiters

run_path = os.getcwd()

def process_args()->argparse.Namespace:
    parser = argparse.ArgumentParser(description='OSDOCR - Clean OCR')
    parser.add_argument('ocr_results',                              type=str, nargs=1,                                          help='target ocr results to clean')
    parser.add_argument('-t', '--target',                           type=str, nargs=1,                                          help='target image')
    parser.add_argument('-tbbf', '--toggle_bounding_boxes_fix',                 action='store_false',                           help='Toggle fix ocr bounding boxes (default: True).')
    parser.add_argument('-tubbf', '--toggle_unite_bounding_boxes',              action='store_false',                           help='Toggle unite ocr bounding boxes (default: True).')
    parser.add_argument('-fi', '--find_images',                     type=int, nargs=1, default=[-1],                            help='''find images in ocr results.  
                        Options: 
                            * 0: simple rule based;
                            * 1: use leptonica to find images. Requires target image.;''',choices=[0,1])
    parser.add_argument('-fd', '--find_delimiters',                 type=int, nargs=1, default=[-1],                            help='''find delimiters in ocr results.
                        Options: 
                            * 0: simple rule based;
                            * 1: use leptonica to find delimiters. Requires target image.;''',choices=[0,1])
    parser.add_argument('-tc', '--text_confidence',                type=int, nargs=1, default=[10],                             help='text confidence for ocr result filtering.')
    parser.add_argument('-o', '--output',                           type=str, nargs=1, default=[f'{run_path}/clean_ocr.json'],  help='output path for cleaned ocr results')
    parser.add_argument('-l', '--logs',                                         action='store_true',                            help='Print logs')
    parser.add_argument('-d', '--debug',                                        action='store_true',                            help='Debug mode')


    args = parser.parse_args()
    return args



def main():

    args = process_args()

    ocr_results = OCR_Tree(args.ocr_results[0])
    target_image = args.target[0] if args.target else None
    find_images_flag = args.find_images[0]
    find_delimiters_flag = args.find_delimiters[0]
    text_confidence = args.text_confidence[0]
    output_path = args.output[0]

    # check if output path exists
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)

    # find images if flag is set
    if find_images_flag:
        if find_images_flag == 1 and target_image:
            # use leptonica to find images
            images = identify_document_images(target_image,logs=args.logs)
            # add images to ocr results
            page = ocr_results.get_boxes_level(1)[0]
            for image in images:
                ocr_image = OCR_Tree({'level':2,'box':image,'type':'image'})
                ocr_image.image_id = image['id']
                page.add_child(ocr_image)
            
        else:
            find_images_flag = 0


    # find delimiters if flag is set
    if find_delimiters_flag:
        if find_delimiters_flag == 1 and target_image:
            # use leptonica to find delimiters
            delimiters = get_document_delimiters(target_image,logs=args.logs)
            # add delimiters to ocr results
            page = ocr_results.get_boxes_level(1)[0]
            for delimiter in delimiters:
                ocr_delimiter = OCR_Tree({'level':2,'box':delimiter,'type':'delimiter'})
                page.add_child(ocr_delimiter)
            
        else:
            find_delimiters_flag = 0

    if args.toggle_bounding_boxes_fix:
        # clean ocr results
        ocr_results = bound_box_fix(ocr_results=ocr_results,
                                    level=2,
                                    image_info=None,
                                    find_images=find_images_flag==0,
                                    find_delimiters=find_delimiters_flag==0,
                                    logs=args.debug)

    if args.toggle_unite_bounding_boxes:
        ocr_results = unite_blocks(ocr_results,conf=text_confidence,logs=args.debug)
    

    # save ocr results
    result_dict_file = open(output_path,'w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()
    


