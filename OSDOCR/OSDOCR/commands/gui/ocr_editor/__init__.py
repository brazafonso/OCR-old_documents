'''OCR Editor command script'''

import argparse
import os
import sys



run_path = os.getcwd()

def process_args()->argparse.Namespace:
    parser = argparse.ArgumentParser(description='OSDOCR - OCR Editor')
    parser.add_argument('-ti','--target_image',type=str,help='Target image path')
    parser.add_argument('-to','--target_ocr_results',type=str,help='Target ocr results path')
    args = parser.parse_args()
    return args



def main():
    from OSDOCR.gui.ocr_editor.ocr_editor import run_gui

    args = process_args()

    run_gui(input_image_path=args.target_image,input_ocr_results_path=args.target_ocr_results)
    


