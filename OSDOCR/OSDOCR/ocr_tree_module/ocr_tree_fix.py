from typing import Union
import cv2
import numpy as np
from scipy import stats
from .ocr_tree import *
from OSDOCR.ocr_tree_module.ocr_tree_analyser import analyze_text,categorize_boxes,categorize_box
from OSDOCR.aux_utils.box import Box
from pytesseract import Output
from PIL import Image
from document_image_utils.image import binarize_fax
import pytesseract
import jellyfish




def remove_empty_boxes(ocr_results:OCR_Tree,text_confidence:int=10,find_delimiters:bool=True,find_images:bool=True,debug:bool=False)->OCR_Tree:
    '''Removes empty boxes from ocr results.'''
    
    if debug:
        print(f'Removing empty boxes | text_confidence: {text_confidence} | find_delimiters: {find_delimiters} | find_images: {find_images}')
    
    
    i = 0

    ocr_results.id_boxes(level=[2],override=False)
    blocks = ocr_results.get_boxes_level(2)

    # remove blocks that have no text and take more than 80% of image
    ## if no flags for finding delimiters or images are set, remove all empty blocks
    image_box = ocr_results.get_boxes_level(0)[0].box
    image_area = image_box.area()
    for i,block in enumerate(blocks):
        if block.is_empty(conf=text_confidence,only_text=True):
            if block.box.area() >= image_area*0.8:
                if debug:
                    print(f'Removing Box : {block.id} is empty and too big')
                ocr_results.remove_box_id(block.id)
                blocks.pop(i)
                continue

            if not find_delimiters:
                if block.is_delimiter(conf=text_confidence,only_type=True):
                    continue
            
            if not find_images:
                if block.is_image(conf=text_confidence,only_type=True):
                    continue

            if debug:
                print(f'Removing Box : {block.id} is empty')
            ocr_results.remove_box_id(block.id)
            blocks.pop(i)

    return ocr_results



def block_bound_box_fix(ocr_results:OCR_Tree,text_confidence:int=10,find_delimiters:bool=True,find_images:bool=True,debug:bool=False)->OCR_Tree:
    '''Fixes block bounding boxes. Deals with intersections of boxes and overlapping boxes.  
    Args:
        ocr_results (OCR_Tree): ocr results
        text_confidence (int, optional): confidence of text, used for finding empty blocks. Defaults to 10.
        find_delimiters (bool, optional): if True, try to find delimiters using rules, else checks for block type. Defaults to True.
        find_images (bool, optional): if True, try to find images using rules, else checks for block type. Defaults to True.
        
    Returns:
        OCR_Tree: ocr results cleaned
    '''
    i = 0
    current_box = None
    ocr_results.id_boxes(level=[2],override=False)
    text_analysis = analyze_text(ocr_results,conf=text_confidence)
    blocks = ocr_results.get_boxes_level(2)

    og_len = len(blocks)
    
    boxes_to_check = {}
    checked_boxes = []
    i= 0
    # iterate over all block boxes
    # if two boxes of the same level are overlaping, delete the inside one
    # assumes that the inside box is a duplicate of information from outside box
    while i< len(blocks):
        # get current box to analyse
        if not current_box and blocks[i].id not in checked_boxes:
            if (not blocks[i].is_empty(conf=text_confidence)) or\
                  blocks[i].is_delimiter(conf=text_confidence,only_type=find_delimiters == False):
                
                current_box = blocks[i]
                i+=1
            else:
                if debug:
                    print(f'Removing Box : {blocks[i].id} is empty and not a delimiter')
                ocr_results.remove_box_id(blocks[i].id)
                blocks.pop(i)
            continue
        # check if boxes are within each other
        if current_box and blocks[i].id != current_box.id:
            compare_box = blocks[i]

            # compared box inside current box
            if compare_box.is_empty(conf=text_confidence) and compare_box.box.is_inside_box(current_box.box):
                if debug:
                    print(f'Removing Box : {compare_box.id} is inside {current_box.id}')
                ocr_results.remove_box_id(compare_box.id)
                if compare_box.id in boxes_to_check: 
                    del boxes_to_check[compare_box.id]
            # current box inside compared box
            elif current_box.is_empty(conf=text_confidence) and current_box.box.is_inside_box(compare_box.box):
                if debug:
                    print(f'Removing Box : {current_box.id} is inside {compare_box.id}')
                ocr_results.remove_box_id(current_box.id)
                current_box = None
            # boxes intersect (with same level, so as to be able to merge seamlessly)
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
                id = keys.pop(0)
                current_box = boxes_to_check[id]
                current_box:OCR_Tree
                del boxes_to_check[id]
                checked_boxes.append(current_box.id)
                # check if box is empty
                # remove if true
                if current_box.is_empty(conf=text_confidence) and \
                    not current_box.is_delimiter(conf=text_confidence,only_type=find_delimiters == False):

                    # if potential image (big box) dont remove
                    if current_box.is_image(conf=text_confidence,text_size=text_analysis['normal_text_size'],
                                            only_type= find_images == False):
                        ocr_results.remove_box_id(current_box.id)
                        current_box = None
                i = 0

    if debug:
        print(f'''
        Initial number of boxes: {og_len}
        Final number of boxes: {len(ocr_results.get_boxes_level(2))}
        ''')
    return ocr_results


def text_bound_box_fix(ocr_results:OCR_Tree,text_confidence:int=10,debug:bool=False)->OCR_Tree:
    '''Fix bound boxes of blocks with text by reducing their sides when confidence of side text is too low.'''

    if debug:
        print('Fixing text bound box')
        print(f'Text confidence: {text_confidence}')

    blocks = ocr_results.get_boxes_level(2)
    text_blocks = [b for b in blocks if b.to_text(conf=text_confidence).strip()]

    for b in text_blocks:
        block_min_left = None
        block_max_right = None
        block_min_top = None
        block_max_bottom = None

        # get adjusted box coordinates
        words = [w for w  in b.get_boxes_level(5,conf=text_confidence) if w.text.strip()]
        if words:
            words = sorted(words,key=lambda w: w.box.left)
            # get left and right
            first_word = words[0]
            last_word = words[-1]
            block_min_left = min(block_min_left,first_word.box.left) if block_min_left else first_word.box.left
            block_max_right = max(block_max_right,last_word.box.right) if block_max_right else last_word.box.right

            # get top and bottom
            words = sorted(words,key=lambda w: w.box.top)
            first_word = words[0]
            last_word = words[-1]
            block_min_top = min(block_min_top,first_word.box.top) if block_min_top else first_word.box.top
            block_max_bottom = max(block_max_bottom,last_word.box.bottom) if block_max_bottom else last_word.box.bottom


        # update box
        if block_min_left and block_max_right and block_min_top and block_max_bottom and \
              (b.box.left < block_min_left or b.box.right > block_max_right or b.box.top < block_min_top or b.box.bottom > block_max_bottom):
            new_left = max(b.box.left,block_min_left)
            new_right = min(b.box.right,block_max_right)
            new_top = max(b.box.top,block_min_top)
            new_bottom = min(b.box.bottom,block_max_bottom)
            if debug:
                print(f'Updating box {b.id} with min left {new_left} and max right {new_right} and min top {new_top} and max bottom {new_bottom}| Old box: {b.box}')
            b.update_box(left=new_left,right=new_right,top=new_top,bottom=new_bottom)

    return ocr_results





def bound_box_fix(ocr_results:OCR_Tree,level:int,image_info:Box=None,text_confidence:int=10,
                  find_images:bool=True,find_delimiters:bool=True,debug:bool=False)->OCR_Tree:
    '''Fix bound boxes\n
    Mainly overlaping boxes'''
    new_ocr_results = {}
    if level == 2:
        new_ocr_results = block_bound_box_fix(ocr_results,text_confidence=text_confidence,find_images=find_images,find_delimiters=find_delimiters,debug=debug)
    elif level == 5:
        new_ocr_results = text_bound_box_fix(ocr_results,text_confidence=text_confidence,debug=debug)

    return new_ocr_results


def bound_box_fix_image(ocr_results:OCR_Tree,target_image:Union[str,cv2.typing.MatLike],
                        level:int=5,text_confidence:int=10,debug:bool=False)->OCR_Tree:
    '''Fix bound boxes of blocks by pixel analysis of bounding boxes in image.
    
    For each direction (left, right, top, bottom) we check (iterating on the interesting direction) 
    for the first black pixel that has neighbouring black pixels.'''

    img = None
    if isinstance(target_image,str):
        img = cv2.imread(target_image)
    else:
        img = target_image

    # get image box
    img_box = Box(0,img.shape[1],0,img.shape[0])

    # treat image
    ## binarize
    img = binarize_fax(img)
    ## threshold
    img = cv2.threshold(img, 123, 255, cv2.THRESH_BINARY)[1]
    ## erode - reduce noise
    # kernel = np.ones((3,3),np.uint8)
    # img = cv2.erode(img,kernel,iterations = 1)

    # get all blocks
    blocks = ocr_results.get_boxes_level(level=level,conf=text_confidence)

    # prepare black pixels arrays for better performance
    black_pixels = (img == 0)
    shifted_down = np.roll(black_pixels,1,axis=0)
    shifted_right = np.roll(black_pixels,1,axis=1)
    shifted_up = np.roll(black_pixels,-1,axis=0)
    shifted_left = np.roll(black_pixels,-1,axis=1)
    
    # for each block check finds first black pixels in area, to reduce bounding box
    ## first pixel needs to have black neighbors
    for b in blocks:
        if b.box.width and b.box.height and b.box.is_inside_box(img_box):
            block_image = black_pixels[b.box.top:b.box.bottom,b.box.left:b.box.right]
            new_top = 0
            new_bottom = block_image.shape[0]
            new_left = 0
            new_right = block_image.shape[1]
            # check top
            ## shift up
            shifted_block_image = shifted_up[b.box.top:b.box.bottom,b.box.left:b.box.right]
            ## invalidate last row
            shifted_block_image[-1,:] = False
            ## get candidates
            candidates = np.argwhere(block_image & shifted_block_image)
            ## get first black pixel
            if len(candidates) > 0:
                new_top = candidates[0][0]


            # check bottom
            ## shift down
            shifted_block_image = shifted_down[b.box.top+new_top:b.box.bottom,b.box.left:b.box.right]
            ## invalidate first row
            shifted_block_image[0,:] = False
            ## get candidates
            candidates = np.argwhere(block_image[new_top:] & shifted_block_image)
            ## get first black pixel
            if len(candidates) > 0:
                new_bottom = candidates[-1][0] + new_top

            # check left
            ## shift left
            shifted_block_image = shifted_left[b.box.top:b.box.bottom,b.box.left:b.box.right]
            ## invalidate last column
            shifted_block_image[:,-1] = False
            ## get candidates
            candidates = np.argwhere(block_image & shifted_block_image)
            ## get first black pixel
            if len(candidates) > 0:
                new_left = np.min(candidates[:,1])

            # check right
            ## shift right
            shifted_block_image = shifted_right[b.box.top:b.box.bottom,b.box.left+new_left:b.box.right]
            ## invalidate first column
            shifted_block_image[:,0] = False
            ## get candidates
            candidates = np.argwhere(block_image[:,new_left:] & shifted_block_image)
            ## get first black pixel
            if len(candidates) > 0:
                new_right = np.max(candidates[:,1]) + new_left

            new_top = b.box.top + new_top
            new_bottom = b.box.bottom - (b.box.height - new_bottom)
            new_left = b.box.left + new_left
            new_right = b.box.right - (b.box.width - new_right)

            if new_top == b.box.top and new_bottom == b.box.bottom and new_left == b.box.left and new_right == b.box.right:
                continue

            # make sure new coordinates are valid
            if new_top == new_bottom:
                new_bottom += 1
            if new_left == new_right:
                new_right += 1

            if debug:
                print(f'Updating box {b.id} with left {new_left} and right {new_right} and top {new_top} and bottom {new_bottom} width {new_right - new_left} and height {new_bottom - new_top}| Old box: {b.box}')

            b.update_box(left=new_left,right=new_right,top=new_top,bottom=new_bottom,invert=False)

    return ocr_results





    




def unite_blocks(ocr_results:OCR_Tree,conf:int=10,horizontal_join:bool=True,debug:bool=False)->OCR_Tree:
    '''Unite same type of blocks if they are horizontally aligned and adjacent to each other'''

    
    # get all blocks
    ocr_results.id_boxes(level=[2],override=False)
    blocks = ocr_results.get_boxes_level(2)
    non_visited = [b.id for b in blocks if b.id]
    available_blocks = [b for b in blocks if b.id]
    # get first block
    target_block_id = non_visited.pop(0)
    # iterate over all blocks
    while non_visited:
        united = False # flag if block was united

        target_block = ocr_results.get_box_id(target_block_id,level=2)
        target_block:OCR_Tree
        if debug:
            print(f'Visiting block {target_block_id}',f' Available blocks: {len(available_blocks)}',f' Non visited blocks: {len(non_visited)}')
        # get adjacent bellow blocks
        below_blocks = target_block.boxes_directly_below(available_blocks)
        

        # if below blocks exist
        if below_blocks:
            # filter blocks of same type and horizontally aligned
            same_type_below_blocks = [b for b in below_blocks if b.type == target_block.type]


            # treating text blocks
            if not target_block.is_empty(conf=conf,only_text=True):
                # if block is vertical text, can only unite with vertical text blocks
                if target_block.is_vertical_text(conf=conf):
                    same_type_below_blocks = [b for b in same_type_below_blocks if b.is_vertical_text(conf=conf)]

            # non text blocks
            else:
                target_orientation = target_block.box.get_box_orientation()
                # orientation should be the same
                same_type_below_blocks = [b for b in same_type_below_blocks if b.box.get_box_orientation() == target_orientation]

            aligned_below_blocks = [b for b in same_type_below_blocks if target_block.box.within_horizontal_boxes(b.box,range=0.1,only_self=True)]
            
            # if single block passed, unite with target block
            if len(aligned_below_blocks) == 1:
                if debug:
                    print('Unite with block',aligned_below_blocks[0].id)
                # get bellow block
                below_block = aligned_below_blocks[0]
                joined_area = target_block.box.copy()
                joined_area.join(below_block.box)
                # check if joined area conflicts with other blocks
                ## if conflicts with other blocks, continue
                if len([b for b in ocr_results.get_boxes_intersect_area(joined_area,level=2)\
                        if b.id not in [target_block.id,below_block.id]]) > 0:
                    pass
                else:
                    # remove bellow block
                    available_blocks = [b for b in available_blocks if b.id != below_block.id]
                    non_visited = [id for id in non_visited if id != below_block.id]

                    # unite
                    target_block.join_trees(below_block)

                    # remove bellow block from main tree
                    ocr_results.remove_box_id(below_block.id,level=2)

                    united = True

            # no aligned blocks, but all below blocks are of same type
            ## join them horizontally, and then unite with target block
            elif len(aligned_below_blocks) == len(same_type_below_blocks) and len(same_type_below_blocks) == len(below_blocks):
                if horizontal_join:
                    if debug:
                        print('Horizontal join of below blocks')

                    # check if joined area conflicts with other blocks
                    ## if conflicts with other blocks, continue
                    joined_area = target_block.box.copy()
                    for b in same_type_below_blocks:
                        joined_area.join(b.box)
                    if len([b for b in ocr_results.get_boxes_intersect_area(joined_area,level=2)\
                            if b.id not in [target_block.id] + [b.id for b in same_type_below_blocks]]) > 0:
                        pass
                    else:
                        # join below blocks horizontally
                        leftmost_block = min(same_type_below_blocks,key=lambda b:b.box.left)
                        leftmost_block:OCR_Tree
                        # remove from main tree and lists
                        same_type_below_blocks.remove(leftmost_block)
                        available_blocks.remove(leftmost_block)
                        non_visited = [id for id in non_visited if id != leftmost_block.id]
                        ocr_results.remove_box_id(leftmost_block.id,level=2)
                        while same_type_below_blocks:
                            next_block = min(same_type_below_blocks,key=lambda b:b.box.left)
                            if debug:
                                print(f'Horizontal join | {leftmost_block.id} -> {next_block.id}')
                            # remove from main tree and lists
                            same_type_below_blocks.remove(next_block)
                            available_blocks.remove(next_block)
                            non_visited = [id for id in non_visited if id != next_block.id]
                            ocr_results.remove_box_id(next_block.id,level=2)
                            leftmost_block.join_trees(next_block,orientation='horizontal')

                        if debug:
                            print('Unite with block',leftmost_block.id)
                        # unite
                        target_block.join_trees(leftmost_block)
                        united = True

        # if block was not united, go to next block
        ## else repeat same block
        if not united:
            target_block_id = non_visited.pop(0)

    return ocr_results



def delimiters_fix(ocr_results:OCR_Tree,conf:int=10,logs:bool=False,debug:bool=False)->OCR_Tree:
    '''Fix delimiters. Adjust bounding boxes, and remove delimiters inside text.'''

    if logs:
        print('Fix delimiters')
        print('Original boxes:',len(ocr_results.get_boxes_level(2)))

    # id boxes
    ocr_results.id_boxes(level=[2],override=False)

    delimiters = ocr_results.get_boxes_type(level=2,types=['delimiter'])
    blocks =  [b for b in ocr_results.get_boxes_level(2,ignore_type=['delimiter']) if not b.is_empty(conf=conf,only_text=True) or b.is_image(only_type=True)]

    if logs:
        print('Blocks:',len(blocks))
        print('Delimiters:',len(delimiters))

    # for each delimiter
    ## check if intersects with other blocks
    ### in which case adjust bounding box
    ## check if inside other blocks
    ### in which case remove delimiter
    for delimiter in delimiters:
        current_delimiter_box = delimiter.box
        current_delimiter_id = delimiter.id
        current_delimiter_orientation = current_delimiter_box.get_box_orientation()
        j = 0
        while j < len(blocks):
            block = blocks[j]
            # inside other blocks
            if current_delimiter_box.is_inside_box(block.box):
                if debug:
                    print(f'Delimiter {current_delimiter_id} inside block {block.id}')
                    
                # inside non-text block, remove delimiter
                if block.is_empty(conf=conf,only_text=True):
                    if debug:
                        print(f'Removing delimiter {current_delimiter_id} inside block {block.id}')
                    ocr_results.remove_box_id(current_delimiter_id,level=2)
                    break
                else:
                    # inside text block
                    ## if within area with no text and has text above and below, split block horizontally in two and keep delimiter
                    extended_delimiter_box = current_delimiter_box.copy()
                    extended_delimiter_box.left = block.box.left
                    extended_delimiter_box.right = block.box.right
                    ## get text above and below
                    above_area = block.box.copy()
                    above_area.bottom = current_delimiter_box.top
                    above_text_blocks = block.get_boxes_intersect_area(above_area,level=5,conf=conf)
                    below_area = block.box.copy()
                    below_area.top = current_delimiter_box.bottom
                    below_text_blocks = block.get_boxes_intersect_area(below_area,level=5,conf=conf)
                    ## remove from below_text_blocks blocks that are in above_text_blocks
                    below_text_blocks = [b for b in below_text_blocks if b not in above_text_blocks]
                    if len(block.get_boxes_intersect_area(extended_delimiter_box,level=5,conf=conf,area_ratio=0.4)) == 0\
                            and len(above_text_blocks) > 0 and len(below_text_blocks) > 0:
                        if debug:
                            print(f'Splitting block {block.id} into two')

                        split_blocks = split_block(block,current_delimiter_box,orientation='horizontal',
                                                   conf=conf,keep_all=True,debug=debug)

                        if len(split_blocks) > 1:
                            block_2 = split_blocks[1]
                            # add new blocks
                            page = ocr_results.get_boxes_level(1)[0]
                            page.add_child(block_2)
                            # add blocks to list
                            blocks.append(block_2)
                            # id boxes again
                            ocr_results.id_boxes(level=[2],override=False)

                    ## remove delimiter
                    else:
                        if debug:
                            print(f'Removing delimiter {current_delimiter_id} inside text block {block.id}')
                        ocr_results.remove_box_id(current_delimiter_id,level=2)

                        break

            # intersects with other blocks
            elif current_delimiter_box.intersects_box(block.box):
                # intercepting with image, probably is a border of a canvas
                if block.is_image(only_type=True):
                    intercept_area = block.box.intersect_area_box(current_delimiter_box).area()
                    delimiter_area = current_delimiter_box.area()
                    ## if more than 50% of delimiter is inside image, remove delimiter
                    if intercept_area/delimiter_area >= 0.5:
                        if debug:
                            print(f'Removing delimiter {current_delimiter_id} inside image {block.id}')
                        ocr_results.remove_box_id(current_delimiter_id,level=2)
                        break
                    else:
                        # adjust delimiter
                        current_delimiter_box.remove_box_area(block.box)
                else:
                    # cut block in two
                    ## get level 3 blocks in area
                    ### if delimiter is horizontal, cut area horizontally
                    extended_delimiter_box = current_delimiter_box.copy()
                    if current_delimiter_orientation == 'horizontal':
                        extended_delimiter_box.left = block.box.left
                        extended_delimiter_box.right = block.box.right
                    ### if delimiter is vertical, cut area vertically
                    else:
                        extended_delimiter_box.top = block.box.top
                        extended_delimiter_box.bottom = block.box.bottom

                    # if delimiter passes through block, check block text if able to cut block in two
                    text_in_area = block.get_boxes_intersect_area(extended_delimiter_box,level=5,conf=conf,area_ratio=0.4)
                    if len(text_in_area) > 0:
                        # can't cut block in two
                        ## just adjust bounding box
                        ### check if adjust block or delimiter
                        if current_delimiter_orientation == 'horizontal':
                            if block.box.right < current_delimiter_box.left or block.box.left > current_delimiter_box.right:
                                # adjust block
                                if debug:
                                    print(f'Adjusting bounding box of block {block.id} | intersection with delimiter {current_delimiter_id}')       
                                block.box.remove_box_area(current_delimiter_box)
                            else:
                                # adjust delimiter
                                if debug:
                                    print(f'Adjusting bounding box of delimiter {current_delimiter_id} | intersection with block {block.id}')
                                current_delimiter_box.remove_box_area(block.box)
                        else:
                            if block.box.top > current_delimiter_box.top or block.box.bottom < current_delimiter_box.bottom:
                                # adjust block
                                if debug:
                                    print(f'Adjusting bounding box of block {block.id} | intersection with delimiter {current_delimiter_id}')  
                                block.box.remove_box_area(current_delimiter_box)
                            else:
                                # adjust delimiter
                                if debug:
                                    print(f'Adjusting bounding box of delimiter {current_delimiter_id} | intersection with block {block.id}')
                                current_delimiter_box.remove_box_area(block.box)
                    else:
                        if debug:
                            print(f'Can cut block {block.id} in two with delimiter {current_delimiter_id}')
                        new_blocks = split_block(block,current_delimiter_box,current_delimiter_orientation,conf=conf,debug=debug)

                        block_1 = new_blocks[0]

                        if len(new_blocks) > 1:
                            block_2 = new_blocks[1]
                            # add new blocks
                            page = ocr_results.get_boxes_level(1)[0]
                            page.add_child(block_2)
                            # add blocks to list
                            blocks.append(block_2)
                            # id boxes again
                            ocr_results.id_boxes(level=[2],override=False)

            j += 1

    if logs:
        print('Remaining boxes:',len(ocr_results.get_boxes_level(2)))

    return ocr_results



def remove_solo_words(ocr_results:OCR_Tree,conf:int=10,debug:bool=False)->OCR_Tree:
    '''Remove boxes with single words that are inside of other boxes. Bloxes need to be IDed and typed before calling this function.'''

    blocks = ocr_results.get_boxes_level(2)

    i = 0
    while i < len(blocks):
        block = blocks[i]
        if not block.is_empty(conf=conf):
            text = block.to_text(conf=conf)
            # check if text is single word and inside of other boxes of different type
            if len(text.strip().split(' ')) == 1:
                for b in blocks:
                    if b.id != block.id and block.box.is_inside_box(b.box):
                        if b.type != block.type:
                            if debug:
                                print(f'Removing solo word: {block.id} | inside {b.id} | type: {block.type} | {text}')
                            ocr_results.remove_box_id(block.id,level=2)
                            blocks.pop(i)
                            i -= 1
                            break

        i += 1
    return ocr_results



def find_text_titles(ocr_results:OCR_Tree,conf:int=10,id_blocks:bool=True,categorize_blocks:bool=True,debug:bool=False)->OCR_Tree:
    '''From ocr_results, searches within text blocks for titles and separatest them from the rest.
    Potential titles should be lines that are taller than normal text size, and come after closed text, or are in the beggining of the block.'''

    if id_blocks:
        ocr_results.id_boxes(level=[2],override=False)

    if categorize_blocks:
        ocr_results = categorize_boxes(ocr_results,conf=conf,debug=debug)

    ocr_analysis = analyze_text(ocr_results,conf=conf)

    page = ocr_results.get_boxes_level(1)[0]
    blocks = [b for b in ocr_results.get_boxes_level(2) if b.type != 'title' and not b.is_empty(conf=conf)]

    if blocks == []:
        return ocr_results

    last_id = sorted([b.id for b in blocks])[-1] + 1
    i = 0
    # find titles in text blocks
    while i < len(blocks):
        block = blocks[i]
        # id lines in block
        block.id_boxes(level=[4])
        lines = block.get_boxes_level(4)
        if len(lines) < 2:
            i += 1
            continue
        j = 0
        for j,line in enumerate(lines):
            potential_title = []
            line_category = categorize_box(line,blocks,ocr_analysis,conf=conf)
            if line_category == 'title':
                if j > 0:
                    last_line = lines[j-1]
                    last_line_text = last_line.to_text(conf=conf).strip()
                else:
                    last_line_text = ''
                # check if last line is ended
                if not re.search(r'[\d\w]+',last_line_text) or last_line_text[-1] in ['.','?','!']:
                    potential_title.append(line)
                    # check next lines for title continuation
                    for j in range(j+1,len(lines)):
                        next_line = lines[j]
                        next_line_category = categorize_box(next_line,blocks,ocr_analysis,conf=conf)
                        if next_line_category == 'title':
                            potential_title.append(next_line)
                        else:
                            break
            if potential_title:
                # adjust current blocks and create new title block
                ## create new title block
                title_block = OCR_Tree({'level':2,'box':potential_title[0].box,'type':'title','id':last_id})
                ### create paragraph for lines
                title_block_par = OCR_Tree({'level':3,'box':potential_title[0].box.copy()})
                ### add lines to paragraph
                for line in potential_title:
                    title_block_par.add_child(line.copy())
                ### add paragraph to title block
                title_block.add_child(title_block_par)
                ### add title block to ocr results
                page.add_child(title_block)
                last_id += 1

                if debug:
                    print(f'Found title: {title_block.to_text(conf=conf)}')

                ## adjust current blocks
                new_blocks = split_block(block,title_block.box,orientation='horizontal',conf=conf,debug=debug)
                print(new_blocks[0].to_text(conf=conf))

                if len(new_blocks) > 1:
                    print(new_blocks[1].to_text(conf=conf))
                    # add new block
                    new_block = new_blocks[-1]
                    new_block.id = last_id
                    new_block.type = 'text'
                    last_id += 1
                    page.add_child(new_block)
                    blocks.append(new_block)

                break
            j += 1

        i += 1
    return ocr_results




def split_block(block:OCR_Tree,delimiter:Box,orientation:str='horizontal',conf:int=10,keep_all:bool=False,debug:bool=False)->list['OCR_Tree']:
    '''Splits block into new blocks, based on delimiter and cut direction. Adjust text inside blocks to fit new area.'''
    new_blocks = [block]

    if debug:
        print(f'Block 1 | Original children len: {len(block.children)}')
        print(f'Delimiter: {delimiter}')

    if not delimiter.intersects_box(block.box,inside=True):
        return new_blocks

    if debug:
        print(f'Splitting block {block.id}')

    if orientation not in ['horizontal','vertical']:
        orientation = 'horizontal'


    if orientation == 'horizontal':
        if debug:
            print('Splitting block by x')

        area_1 = Box({'left':block.box.left, 'top':block.box.top, 'right':block.box.right, 'bottom':min(block.box.bottom,delimiter.top+1)})
        area_2 = Box({'left':block.box.left, 'top':delimiter.bottom, 'right':block.box.right, 'bottom':block.box.bottom})
    elif orientation == 'vertical':
        if debug:
            print('Splitting block by y')

        area_1 = Box({'left':block.box.left, 'top':block.box.top, 'right':max(delimiter.left,block.box.left+1), 'bottom':block.box.bottom})
        area_2 = Box({'left':delimiter.right, 'top':block.box.top, 'right':block.box.right, 'bottom':block.box.bottom})


    if debug:
        print(f'Area 1: {area_1}')
        print(f'Area 2: {area_2}')

    # update first block
    blocks_1 = []
    blocks_2 = []
    ## blocks need to be gathered according to delimter orientation (division cut)
    ### if horizontal 
    #### gather all lines and check which belong to what area
    #### create new paragraphs according to lines
    ### if vertical
    #### gather all lines and paragraphs
    #### for each line check what words belong to what area

    # id words
    block.id_boxes(level=[3,4,5])
    blocks_1 = [b.copy() for b in block.get_boxes_level(3)]
    blocks_2 = [b.copy() for b in block.get_boxes_level(3)]
    # only leave each word in one of the areas
    for i,p in enumerate(blocks_1):
        par_words = p.get_boxes_level(5)
        for w in par_words:
            if w.box.is_inside_box(area_1):
                blocks_2[i].remove_box_id(w.id,level=5)
            elif w.box.is_inside_box(area_2):
                blocks_1[i].remove_box_id(w.id,level=5)
            elif keep_all:
                # add to area with biggest intersection
                if area_1.intersect_area_box(w.box).area() > area_2.intersect_area_box(w.box).area():
                    blocks_2[i].remove_box_id(w.id,level=5)
                else:
                    blocks_1[i].remove_box_id(w.id,level=5)
            else:
                blocks_2[i].remove_box_id(w.id,level=5)
                blocks_1[i].remove_box_id(w.id,level=5)

        # remove empty lines
        lines_1 = blocks_1[i].get_boxes_level(4)
        lines_2 = blocks_2[i].get_boxes_level(4)

        for l in lines_1:
            if l.is_empty(conf=conf,only_text=True):
                blocks_1[i].remove_box_id(l.id,level=4)

        for l in lines_2:
            if l.is_empty(conf=conf,only_text=True):
                blocks_2[i].remove_box_id(l.id,level=4)

        
        # update par boxes
        blocks_1[i].update_box(right=area_1.right)
        blocks_2[i].update_box(left=area_2.left)

    # remove empty pars
    blocks_1 = [b for b in blocks_1 if not b.is_empty(conf=conf,only_text=True)]
    blocks_2 = [b for b in blocks_2 if not b.is_empty(conf=conf,only_text=True)]

    if blocks_1:
        # update current block
        ## box 
        block.box.update(left=area_1.left,top=area_1.top,right=area_1.right,bottom=area_1.bottom,invert=False)
        
        ## children
        block.children = []
        for b in blocks_1:
            block.add_child(b)

        if debug:
            print(f'Block 1 | New children len: {len(block.children)}')

        block.update_box(left=area_1.left,top=area_1.top,right=area_1.right,bottom=area_1.bottom)

        if debug:
            print(f'Block 1 | New box: {block.box}')
    
    if blocks_2:

        if not blocks_1:
            # update current block with area 2
            block.box.update(left=area_2.left,top=area_2.top,right=area_2.right,bottom=area_2.bottom,invert=False)

            if debug:
                print(f'Area 1 is empty. Update block with area 2')

            block.children = []
            for b in blocks_2:
                block.add_child(b)

            if debug:
                print(f'Block 1 | New children len: {len(block.children)}')

            block.update_box(left=area_2.left,top=area_2.top,right=area_2.right,bottom=area_2.bottom)

            if debug:
                print(f'Block 1 | New box: {block.box}')


        else:
            # create second block
            new_block = OCR_Tree({'level':block.level,'box':area_2.copy()})
            
            for b in blocks_2:
                new_block.add_child(b)

            if debug:
                print(f'Block 2 | New children len: {len(new_block.children)}')
            new_block.update_box(left=area_2.left,top=area_2.top,right=area_2.right,bottom=area_2.bottom)

            new_blocks = [block,new_block]

            if debug:
                print(f'Block 2 | New box: {new_block.box}')
    

    return new_blocks



def split_whitespaces(ocr_results:OCR_Tree,conf:int=10,dif_ratio:int=3,debug:bool=False)->OCR_Tree:
    '''If a block contains sequence of whitespaces of ratio 'dif_ratio' compared to normal word distance, split the block into two blocks.
    
    Only possible if block has single line, or every line has similar amount of whitespaces in the same position.'''

    if debug:
        print('Splitting whitespaces...')

    text_analysis = analyze_text(ocr_results,conf=conf)
    avg_word_dist = text_analysis['average_word_distance']

    # id blocks
    ocr_results.id_boxes(level=[2],override=False)

    # get blocks with text
    blocks = [b for b in ocr_results.get_boxes_level(2) if not b.is_empty(conf=conf,only_text=True)]
    last_id = max(ocr_results.get_boxes_level(2),key=lambda b:b.id).id + 1

    # blocks.sort(key=lambda b:b.id)
    for block in blocks:

        # get lines
        lines = block.get_boxes_level(4)
        lines_seq_positions = []     # list of positions of whitespaces in each line
        valid_split = True

        # for each line, check if it contains a valid sequence of whitespaces
        ## saves the coordinates of the first and last whitespace in the sequence
        for line in lines:
            line_words = line.get_boxes_level(5,conf=conf)
            line_seq_positions = [] # list of positions of whitespaces in the line
            line_word_dists = []
            line_word_pairs = []

            # add first distance
            if len(line_words) > 0:
                line_word_dists.append(line_words[0].box.left - block.box.left)
                line_word_pairs.append((block,line_words[0]))

            for i,word in enumerate(line_words[:-1]):
                line_word_dists.append(line_words[i+1].box.left - word.box.right)
                line_word_pairs.append((word,line_words[i+1]))

            # add last distance
            if len(line_words) > 0:
                line_word_dists.append(block.box.right - line_words[-1].box.right)
                line_word_pairs.append((line_words[-1],block))

            # identify word distance outliers
            j = 0
            while j < len(line_word_dists[1:-1]):
                if line_word_dists[j+1] <= 0:
                    line_word_dists.pop(j+1)
                    line_word_pairs.pop(j+1)
                else:
                    j += 1

            if line_word_dists:
                # get average (adjusted with overall word distance)
                average = (sum(line_word_dists)/len(line_word_dists)*0.3 + avg_word_dist*0.7)/2
                # check if any of the dists are bigger than 'dif_ratio' times the median
                for i,d in enumerate(line_word_dists):
                    line_seq_position = [None,None]
                    if d >= dif_ratio*average:
                        if i == 0:
                            line_seq_position[0] = block.box.left
                            line_seq_position[1] = line_word_pairs[i][1].box.left
                        elif i == len(line_word_dists)-1:
                            line_seq_position[0] = line_word_pairs[i][0].box.right
                            line_seq_position[1] = block.box.right
                        else:
                            line_seq_position[0] = line_word_pairs[i][0].box.right
                            line_seq_position[1] = line_word_pairs[i][1].box.left

                        line_seq_positions.append(line_seq_position)

                if not line_seq_positions:
                    valid_split = False
                    break
                else:
                    lines_seq_positions.append(line_seq_positions)

        if valid_split and len(lines_seq_positions) == len(lines):
            if debug:
                print(f'Valid split found for block {block.id} | nº of lines: {len(lines)}')

            # check max matching coordinates for split
            ## check for all intervals of first line, if any intercepts with at least one interval of the other lines
            interception = False
            intersecting_intervals = []
            intervals_path = []
            for first_line_interval in lines_seq_positions[0]:

                intervals_path = [first_line_interval]
                intersecting_intervals = [[first_line_interval]]
                i = 1
                # get all other line intervals that intersect 
                while i < len(lines_seq_positions):
                    line_intersection_intervals = []
                    for other_line_interval in lines_seq_positions[i]:
                        if first_line_interval[0] <= other_line_interval[1] and other_line_interval[0] <= first_line_interval[1]:
                            line_intersection_intervals.append(other_line_interval)

                    if line_intersection_intervals:
                        intersecting_intervals.append(line_intersection_intervals)
                    else:
                        break

                    i += 1

                # check if at least one interval in all other lines intersects
                if len(intersecting_intervals) != len(lines):
                    continue

                # check if for each interval in other lines, at least one interval in remaining lines intersects
                ## for current target_interval, check the next line for interval with intersection, and so forth until last line
                i = 0
                j = [0]*len(lines_seq_positions)
                found_intersection = False
                while i < len(intersecting_intervals) - 1 and i >= 0:
                    found_intersection = False
                    if j[i] >= len(intersecting_intervals[i]):
                        i -= 1
                        j[i] += 1
                        continue

                    target_interval = intersecting_intervals[i][j[i]]
                    i += 1
                    comparing_intervals = intersecting_intervals[i]
                    # compare with intervals of next line
                    k = j[i]
                    while k < len(comparing_intervals):
                        comparing_interval = comparing_intervals[k]
                        if target_interval[0] <= comparing_interval[1] and comparing_interval[0] <= target_interval[1]:
                            j[i] = k
                            found_intersection = True
                            break

                        k += 1
                    
                    # if no intersection found, go to previous line and try next interval
                    if not found_intersection:
                        i -= 1
                        j[i] += 1

                if found_intersection:
                    interception = True
                    # add intervals to path
                    for i in range(1,len(j)):
                        intervals_path.append(intersecting_intervals[i][j[i]])

                    break

                         
            ## if all intervals intercept, check widest common interval
            if interception:
                if debug:
                    print(f'Valid split found for block {block.id} | nº of lines: {len(lines)}')
                left = intervals_path[0][0]
                right = intervals_path[0][1]
                for interval in intervals_path:
                    if interval[0] > left:
                        left = interval[0]
                    if interval[1] < right:
                        right = interval[1]

                # check if interval is wide enough
                d = right - left
                if d >= dif_ratio*average:
                    # split block
                    delimiter = Box(left,right,block.box.top,block.box.bottom)
                    blocks = split_block(block,delimiter,orientation='vertical',keep_all=True,conf=conf,debug=debug)
                    new_block = blocks[1] if len(blocks) == 2 else None

                    if debug:
                        print(f'Block: {block.id} | Box: {block.box}')

                    # add new block
                    if new_block:
                        new_block.id = last_id
                        if debug:
                            print(f'Adding new block {new_block.id} | Box: {new_block.box}')
                        last_id += 1
                        page = ocr_results.get_boxes_level(1)[0]
                        page.add_child(new_block)
                        blocks.append(new_block)
                    else:
                        if debug:
                            print('No new block added')

    return ocr_results




