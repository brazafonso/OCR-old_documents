from ocr_box_module.ocr_box import *
from ocr_box_module.ocr_box_analyser import *
from aux_utils.box import Box

def block_bound_box_fix(ocr_results:OCR_Box):
    '''Fix block bound boxes\n'''
    i = 0
    current_box = None
    text_analysis = analyze_text(ocr_results)
    blocks = ocr_results.get_boxes_level(2)
    boxes_to_check = {}
    checked_boxes = []
    og_len = len(blocks)
    # iterate over all block boxes
    # if two boxes of the same level are overlaping, delete the inside one
    # assumes that the inside box is a duplicate of information from outside box
    while i< len(blocks):
        # get current box to analyse
        if not current_box and blocks[i].id not in checked_boxes:
            if (not blocks[i].is_empty()) or blocks[i].is_delimiter():
                current_box = blocks[i]
                i+=1
            else:
                ocr_results.remove_box_id(blocks[i].id)
                blocks.pop(i)
            continue
        # check if boxes are within each other
        if current_box and blocks[i].id != current_box.id:
            #print('Comparing boxes',current_box.id,blocks[i].id)
            compare_box = blocks[i]

            # compared box inside current box
            if compare_box.box.is_inside_box(current_box.box):
                ocr_results.remove_box_id(compare_box.id)
                if compare_box.id in boxes_to_check: 
                    del boxes_to_check[compare_box.id]
            # current box inside compared box
            elif current_box.box.is_inside_box(compare_box.box):
                ocr_results.remove_box_id(current_box.id)
                current_box = None
            # boxes intersect (with same level, so as to be able to merge seemlessly)
            elif current_box.box.intersects_box(compare_box.box) and current_box.box.same_level_box(compare_box.box):
                intersect_area = current_box.box.intersect_area_box(compare_box.box)
                # update boxes so that they don't intersect
                # smaller box is reduced
                if current_box.box.box_is_smaller(compare_box.box):
                    current_box.box.remove_box_area(intersect_area)
                else:
                    compare_box.box.remove_box_area(intersect_area)
            else:
                if compare_box.id not in checked_boxes and compare_box.id not in boxes_to_check:
                    boxes_to_check[compare_box.id] = compare_box
        i+=1
        # change current box to next one
        if (i == len(blocks) and boxes_to_check) or (not current_box and boxes_to_check):
            current_box = None
            keys = list(boxes_to_check.keys())
            # get next not empty block
            while not current_box and boxes_to_check:
                id = keys.pop(0)
                current_box = boxes_to_check[id]
                del boxes_to_check[id]
                checked_boxes.append(current_box.id)
                # check if box is empty
                # remove if true
                if current_box.is_empty() and not current_box.is_delimiter():
                    # if potential image (big box) dont remove
                    if not current_box.box.height > text_analysis['normal_text_size']*3:
                        ocr_results.remove_box_id(current_box.id)
                        current_box = None
                i = 0


    print(f'''
    Initial number of boxes: {og_len}
    Final number of boxes: {len(ocr_results.get_boxes_level(2))}
    ''')
    return ocr_results


def bound_box_fix(ocr_results:OCR_Box,level:int,image_info:Box):
    '''Fix bound boxes\n
    Mainly overlaping boxes'''
    new_ocr_results = {}
    if level == 2:
        new_ocr_results = block_bound_box_fix(ocr_results)

    return new_ocr_results