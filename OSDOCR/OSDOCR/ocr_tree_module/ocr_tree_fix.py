from .ocr_tree import *
from .ocr_tree_analyser import *
from OSDOCR.aux_utils.box import Box

def block_bound_box_fix(ocr_results:OCR_Tree,find_delimiters:bool=True,find_images:bool=True,logs:bool=False)->OCR_Tree:
    '''Fix block bound boxes\n'''
    i = 0
    current_box = None
    text_analysis = analyze_text(ocr_results)
    blocks = ocr_results.get_boxes_level(2)

    
    # remove blocks that have no text and take more than 80% of image
    image_box = ocr_results.get_boxes_level(0)[0].box
    image_area = image_box.area()
    for i,block in enumerate(blocks):
        if block.is_empty():
            if block.box.area() >= image_area*0.8:
                if logs:
                    print(f'Removing Box : {block.id} is empty and too big')
                ocr_results.remove_box_id(block.id)
                blocks.pop(i)



    boxes_to_check = {}
    checked_boxes = []
    og_len = len(blocks)
    # iterate over all block boxes
    # if two boxes of the same level are overlaping, delete the inside one
    # assumes that the inside box is a duplicate of information from outside box
    while i< len(blocks):
        # get current box to analyse
        if not current_box and blocks[i].id not in checked_boxes:
            if (not blocks[i].is_empty()) or blocks[i].is_delimiter(only_type=find_delimiters == False):
                current_box = blocks[i]
                i+=1
            else:
                if logs:
                    print(f'Removing Box : {blocks[i].id} is empty and not a delimiter')
                ocr_results.remove_box_id(blocks[i].id)
                blocks.pop(i)
            continue
        # check if boxes are within each other
        if current_box and blocks[i].id != current_box.id:
            #print('Comparing boxes',current_box.id,blocks[i].id)
            compare_box = blocks[i]

            # compared box inside current box
            if compare_box.is_empty() and compare_box.box.is_inside_box(current_box.box):
                if logs:
                    print(f'Removing Box : {compare_box.id} is inside {current_box.id}')
                ocr_results.remove_box_id(compare_box.id)
                if compare_box.id in boxes_to_check: 
                    del boxes_to_check[compare_box.id]
            # current box inside compared box
            elif current_box.is_empty() and current_box.box.is_inside_box(compare_box.box):
                if logs:
                    print(f'Removing Box : {current_box.id} is inside {compare_box.id}')
                ocr_results.remove_box_id(current_box.id)
                current_box = None
            # boxes intersect (with same level, so as to be able to merge seemlessly)
            elif current_box.box.intersects_box(compare_box.box):
                # update boxes so that they don't intersect
                # smaller box is reduced
                if current_box.box.box_is_smaller(compare_box.box):
                    intersect_area = compare_box.box.intersect_area_box(current_box.box)
                    #print(f'Box {current_box.id} is smaller than {compare_box.id}')
                    current_box.box.remove_box_area(intersect_area)
                    # update current box's children
                    current_box.prune_children_area()
                else:
                    intersect_area = current_box.box.intersect_area_box(compare_box.box)
                    #print(f'Box {compare_box.id} is smaller than {current_box.id}')
                    compare_box.box.remove_box_area(intersect_area)
                    # update compare box's children
                    compare_box.prune_children_area()
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
                current_box = boxes_to_check[id]
                current_box:OCR_Tree
                id = keys.pop(0)
                del boxes_to_check[id]
                checked_boxes.append(current_box.id)
                # check if box is empty
                # remove if true
                if current_box.is_empty() and not current_box.is_delimiter(only_type=find_delimiters == False):
                    # if potential image (big box) dont remove
                    if current_box.is_image(text_size=text_analysis['normal_text_size'],only_type= find_images == False):
                        ocr_results.remove_box_id(current_box.id)
                        current_box = None
                i = 0

    if logs:
        print(f'''
        Initial number of boxes: {og_len}
        Final number of boxes: {len(ocr_results.get_boxes_level(2))}
        ''')
    return ocr_results


def bound_box_fix(ocr_results:OCR_Tree,level:int,image_info:Box,find_images:bool=True,find_delimiters:bool=True,logs:bool=False)->OCR_Tree:
    '''Fix bound boxes\n
    Mainly overlaping boxes'''
    new_ocr_results = {}
    if level == 2:
        new_ocr_results = block_bound_box_fix(ocr_results,find_images=find_images,find_delimiters=find_delimiters,logs=logs)

    return new_ocr_results



def unite_blocks(ocr_results:OCR_Tree,conf:int=10,logs:bool=False)->OCR_Tree:
    '''Unite same type of blocks if they are horizontally aligned and adjacent to each other'''

    
    # get all blocks
    blocks = ocr_results.get_boxes_level(2)
    non_visited = [b.id for b in blocks if b.id]
    available_blocks = [b for b in blocks if b.id]
    # get first block
    target_block_id = non_visited.pop(0)
    # iterate over all blocks
    while non_visited:
        united = False

        target_block = ocr_results.get_box_id(target_block_id,level=2)
        if logs:
            print(f'Visiting block {target_block_id}',f' Available blocks: {len(available_blocks)}',f' Non visited blocks: {len(non_visited)}')
        # get adjacent bellow blocks
        bellow_blocks = target_block.boxes_directly_below(available_blocks)
        

        # if bellow blocks exist
        if bellow_blocks:
            # filter blocks of same type and horizontally aligned
            bellow_blocks = [b for b in bellow_blocks if b.type == target_block.type and b.box.within_horizontal_boxes(target_block.box,range=0.1)]

            # treating text blocks
            if not target_block.is_empty(conf=conf,only_text=True):
                # if block is vertical text, can only unite with vertical text blocks
                if target_block.is_vertical_text(conf=conf):
                    bellow_blocks = [b for b in bellow_blocks if b.is_vertical_text(conf=conf)]

            # non text blocks
            else:
                target_orientation = target_block.box.get_box_orientation()
                # orientation should be the same
                bellow_blocks = [b for b in bellow_blocks if b.box.get_box_orientation() == target_orientation]

            # if single block passed, unite with target block
            if len(bellow_blocks) == 1:
                if logs:
                    print('Unite with block',bellow_blocks[0].id)
                # get bellow block
                bellow_block = bellow_blocks[0]
                # remove bellow block
                available_blocks = [b for b in available_blocks if b.id != bellow_block.id]
                non_visited = [id for id in non_visited if id != bellow_block.id]

                # unite
                target_block.join_trees(bellow_block)

                # remove bellow block from main tree
                ocr_results.remove_box_id(bellow_block.id,level=2)

                united = True
            
        if not united:
            # next block
            target_block_id = non_visited.pop(0)



    return ocr_results



