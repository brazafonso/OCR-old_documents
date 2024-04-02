import math
import os
import json
import re
from aux_utils.box import Box
'''Module to generalize OCR result into box object\n'''


class OCR_Tree:
    '''Class to represent OCR results as a tree object\n'''
    

    def __init__(self,*args):
        '''Initialize ocr_tree object\n
        Available constructors:\n
        ocr_tree(level:int, page_num:int, block_num:int, par_num:int, line_num:int, word_num:int, box:Box, text:str='',conf:int=-1,id=None,type:str=None)\n
        ocr_tree(json_list:list[dict])\n
        ocr_tree(json_file:str)\n'''
        self.level = None # 0 = document, 1 = page, 2 = block, 3 = paragraph, 4 = line, 5 = word
        self.page_num = None
        self.block_num = None
        self.par_num = None
        self.line_num = None
        self.word_num = None
        self.box = Box(0,0,0,0) # info about box size and position on page
        self.text = None 
        self.conf = None
        self.id = None
        self.type = None # type of box (text, image ,delimiter, table, etc)
        self.children = []
        self.parent = None
        self.start_text = None
        self.end_text = None
        if len(args) == 1:
            # from args list
            if isinstance(args[0],list):
                self.from_json(args[0])
            # from args dict
            elif isinstance(args[0],dict):
                if isinstance(args[0]['box'],dict):
                    args[0]['box'] = Box(args[0]['box'])
                self.init(**args[0])
            # from file
            elif isinstance(args[0],str):
                if os.path.isfile(args[0]):
                    with open(args[0],'r') as f:
                        self.from_json(json.load(f))
                else:
                    raise FileNotFoundError(f'File {args[0]} not found')
        # normal method
        else:
            self.init(*args)

    def init(self, level:int, page_num:int, block_num:int, par_num:int, line_num:int, 
                 word_num:int, box:Box, text:str='',conf:int=-1,id=None,type:str=None):
        '''Initialize ocr_tree object'''
        self.level = level
        self.page_num = page_num
        self.block_num = block_num
        self.par_num = par_num
        self.line_num = line_num
        self.word_num = word_num
        self.box = box
        self.text = text
        self.conf = conf
        self.id = id
        self.type = type
        self.children = []
        self.parent = None

    def from_json(self,json_list:list[dict]):
        '''Load ocr_results from json list'''
        for k in json_list[0].keys():
            if k != 'box':
                setattr(self,k,json_list[0][k])
            else:
                self.box = Box(json_list[0][k])
        node_stack = [self]
        for i in range(1,len(json_list)):
            current_node = node_stack[-1]
            node = OCR_Tree(json_list[i])
            if node.level == current_node.level + 1:
                current_node.add_child(node)
                node_stack.append(node)
            elif node.level == current_node.level:
                node_stack.pop()
                current_node = node_stack[-1]
                current_node.add_child(node)
                node_stack.append(node)
            else:
                while node.level != current_node.level + 1:
                    node_stack.pop()
                    current_node = node_stack[-1]
                current_node.add_child(node)
                node_stack.append(node)


    def to_json(self):
        data = []
        data.append({
            'level':self.level,
            'page_num':self.page_num,
            'block_num':self.block_num,
            'par_num':self.par_num,
            'line_num':self.line_num,
            'word_num':self.word_num,
            'box':self.box.to_json() if self.box else None,
            'text':self.text,
            'conf':self.conf,
            'id':self.id,
            'type':self.type
        })
        for child in self.children:
            data += child.to_json()
        return data
    
    def to_dict(self,result:dict=None):
        if not result:
            result = {k:[] for k in self.__dict__.keys()}
        for k in self.__dict__.keys():
            if k in ['mean_height']:
                continue
            if k not in ['box']:
                result[k].append(getattr(self,k))
            else:
                result[k].append(self.box.to_dict())
        for child in self.children:
            child.to_dict(result)
        return result

    def copy(self):
        '''Copy ocr_tree object'''
        return OCR_Tree(self.level,self.page_num,self.block_num,self.par_num,self.line_num,self.word_num,self.box,self.text,self.conf,self.id,self.type)
            
        

    def __str__(self):
        return f'ocr_tree(level={self.level},page_num={self.page_num},block_num={self.block_num},par_num={self.par_num},line_num={self.line_num},word_num={self.word_num},box={self.box},text={self.text},conf={self.conf},id={self.id})'

    def pretty_print(self,index:int=0):
        print('  '*index + str(self))
        for child in self.children:
            child.pretty_print(index+1)


    def add_child(self, child):
        '''Add child to ocr_results'''
        child.parent = self
        self.children.append(child)
        self.box.join(child.box)

    def id_boxes(self,level:list[int]=[2],ids:dict=None,delimiters:bool=True,area:Box=None):
        '''Id boxes in ocr_results
        
        Args:
            * level (list[int], optional): Levels to id. Defaults to [2].
            * ids (dict, optional): Dict that saves the current id for each level. Defaults to None.
            * delimiters (bool, optional): If False, only id non delimiters. Defaults to True.
            * area (Box, optional): Area to id boxes. Defaults to None.'''
        if not ids:
            ids = {l:0 for l in level}
        if self.level in level:
            if (delimiters or not self.is_delimiter()) and (not area or self.box.is_inside_box(area)):
                self.id = ids[self.level]
                ids[self.level] += 1
        if self.level < max(level):
            for child in self.children:
                child.id_boxes(level,ids,delimiters,area)

    def clean_ids(self,level:list[int]=[2]):
        '''Clean ids in ocr_results
        
        Args:
            level (list[int], optional): Levels to clean. Defaults to [2].'''
        if self.level in level:
            self.id = None
        if self.level < max(level):
            for child in self.children:
                child.clean_ids(level)

    def get_box_id(self,id:int=0,level:int=2):
        '''Get box with id and level in ocr_results'''
        group_boxes = None
        if self.level == level and self.id == id:
            group_boxes = self
        else:
            for child in self.children:
                if child.level <= level:
                    group_boxes = child.get_box_id(id,level)
                if group_boxes:
                    break
        return group_boxes
    
    def get_boxes_level(self,level:int,ignore_type:list[str]=[])->list['OCR_Tree']:
        '''Get boxes with level in ocr_results'''
        group_boxes = []
        if self.level == level and self.type not in ignore_type:
            group_boxes.append(self)
        else:
            for child in self.children:
                if child.level <= level:
                    group_boxes += child.get_boxes_level(level,ignore_type)
        return group_boxes
    
    def calculate_mean_height(self,level:int=5)->float:
        '''Get mean height of group boxes'''
        line_sum = 0
        count = 0
        boxes_level = self.get_boxes_level(level)
        for box in boxes_level:
            line_sum += box.box.height
            count += 1
        
        return line_sum/count if count > 0 else 0
    
    def is_text_size(self,text_size:float,mean_height:float=None,range:float=0.1,level:int=5):
        '''Check if text size is in range'''
        mean_height = mean_height
        if not mean_height:
            mean_height = self.calculate_mean_height(level)
        if mean_height >= text_size*(1-range) and mean_height <= text_size*(1+range):
            return True
        return False
    
    def is_empty(self,conf:int=0):
        '''Check if box is empty'''
        text = self.to_text(conf).strip()
        empty = re.match(r'^\s*$',text)
        return empty != None
    
    def is_delimiter(self,conf:int=0):
        '''Check if box is delimiter'''
        if self.level == 2 and self.is_empty(conf):
            if self.box.width >= self.box.height*4 or self.box.height >= self.box.width*4:
                return True
        return False
    
    def is_vertical_text(self,conf:int=0):
        '''Check if box is vertical text'''
        if self.level == 2 and not self.is_empty(conf):
            lines = self.get_boxes_level(4)
            # single line
            if len(lines) == 1:
                words = self.get_boxes_level(5)
                # single word
                ## check width and height
                if len(words) == 1:
                    if words[0].box.height >= words[0].box.width*2:
                        return True
                # multiple words
                ## check if most words overlap on x axis
                else:
                    # word with greatest horizontal range
                    widest_word = max(words, key=lambda x: x.box.width)
                    overlapped_words = 0
                    for word in words:
                        if word.box.within_horizontal_boxes(widest_word.box,range=0.1):
                            overlapped_words += 1
                    if overlapped_words/len(words) >= 0.5:
                        return True

            # multiple lines
            ## check if most lines overlap on y axis
            else:
                # line with greatest vertical range
                tallest_line = max(lines, key=lambda x: x.box.height)
                overlapped_lines = 0
                for line in lines:
                    if line.box.within_vertical_boxes(tallest_line.box,range=0.1):
                        overlapped_lines += 1
                
                if overlapped_lines/len(lines) >= 0.5:
                    return True
        return False

    def get_delimiters(self,search_area:Box=None,orientation:str=None,conf:int=0):
        '''Get delimiters in ocr_results\n
        Delimiters are boxes with level 2 and empty text'''
        delimiters = []
        if self.is_delimiter(conf):
            valid = True
            if search_area and not self.box.is_inside_box(search_area):
                valid = False
            if orientation and self.box.get_box_orientation() != orientation:
                valid = False
            if valid:
                delimiters.append(self)
        elif self.level < 2:
            for child in self.children:
                delimiters += child.get_delimiters(search_area,orientation,conf)
        return delimiters
    

    def to_text(self,conf:int=0):
        '''Return text in ocr_results'''
        text = ''
        if self.level == 5 and self.conf >= conf:
            text += self.text + ' '
        elif self.level == 4:
            text += '\n'
        elif self.level == 3:
            text += '\n\t'
        for child in self.children:
            text += child.to_text(conf)
        return text
    
    def remove_box_id(self,id:int,level:int=2):
        '''Remove box in ocr_results with id and level'''
        if self.level == level and self.id == id:
            if self.parent:
                self.parent.children.remove(self)
        else:
            for child in self.children:
                child.remove_box_id(id,level)


    def get_boxes_in_area(self,area:Box,level:int=2,ignore_type:list[str]=[])->list['OCR_Tree']:
        '''Get boxes in area\n
        If level is -1, get all boxes in area'''
        boxes = []
        if area:
            if (level == -1 or self.level == level ) and self.box.is_inside_box(area) and self.type not in ignore_type:
                boxes.append(self)
            elif self.level < level or level == -1:
                for child in self.children:
                    child:OCR_Tree
                    boxes += child.get_boxes_in_area(area,level,ignore_type)
        return boxes
    
    def prune_children_area(self,area:Box=None):
        '''Prune children area so that they are inside box'''
        # is parent
        if not area:
            area = self.box
        # is child, prune
        else:
            if self.box.left < area.left:
                self.box.left = area.left
            if self.box.right > area.right:
                self.box.right = area.right
            if self.box.top < area.top:
                self.box.top = area.top
            if self.box.bottom > area.bottom:
                self.box.bottom = area.bottom
        for child in self.children:
            child.prune_children_area(area)
    

    def type_color(self)->tuple[int,int,int]:
        '''Get block color, in bgr value, based on type
        
        Colors:
            - text: yellow
            - image: black
            - title: red
            - delimiter: blue
            - caption : white
            - other: green'''
        
        if self.type == 'text':
            return (0,255,255)
        elif self.type == 'image':
            return (0,0,0)
        elif self.type == 'title':
            return (0,0,255)
        elif self.type == 'delimiter':
            return (255,0,0)
        elif self.type == 'caption':
            return (255,255,255)
        else:
            return (0,255,0)
        

    def boxes_below(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get blocks below\n
        Get blocks below block, lowest distance, and intersecting with extension of block\n'''

        # extend block vertically
        block_extended = self.box.copy()
        block_extended.top = 0
        block_extended.bottom = 1000000

        # get blocks below block
        below_blocks = [b for b in blocks if b.box.top > self.box.top and b.box.intersects_box(block_extended)]
        return below_blocks
    
    def boxes_right(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get blocks right\n
        Get blocks right block, lowest distance, and intersecting with extension of block\n'''

        # extend block horizontally
        block_extended = self.box.copy()
        block_extended.left = 0
        block_extended.right = 1000000

        # get blocks right block
        right_blocks = [b for b in blocks if b.box.left > self.box.left and b.box.intersects_box(block_extended)]
        return right_blocks
    
    def boxes_above(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get blocks above\n
        Get blocks above block, lowest distance, and intersecting with extension of block\n'''

        # extend block vertically
        block_extended = self.box.copy()
        block_extended.top = 0
        block_extended.bottom = 1000000

        # get blocks above block
        above_blocks = [b for b in blocks if b.box.bottom < self.box.bottom and b.box.intersects_box(block_extended)]
        return above_blocks
    
    def boxes_left(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get blocks left\n
        Get blocks left block, lowest distance, and intersecting with extension of block\n'''

        # extend block horizontally
        block_extended = self.box.copy()
        block_extended.left = 0
        block_extended.right = 1000000

        # get blocks left block
        left_blocks = [b for b in blocks if b.box.right < self.box.right and b.box.intersects_box(block_extended)]
        return left_blocks



    def boxes_directly_below(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get block below\n
        Get block below block, lowest distance, and intersecting with extension of block\n'''

        # extend block vertically
        block_extended = self.box.copy()
        block_extended.top = 0
        block_extended.bottom = 1000000

        # get blocks below block
        below_blocks = [b for b in blocks if b.box.top > self.box.top and not b.box.is_inside_box(self.box) and b.box.intersects_box(block_extended)]
        # print('below blocks',[b.id for b in below_blocks])


        ## clean directly below blocks
        ### make sure no blocks are below directly below blocks
        clean_directly_below_blocks = []
        for b1 in below_blocks:
            valid = True
            for b2 in below_blocks:
                if b2 == b1:
                    continue
                if (b1.box.intersects_box(b2.box,extend_vertical=True,inside=True)) and b1.box.top > b2.box.top:
                    valid = False
                    break
            if valid:
                clean_directly_below_blocks.append(b1)

        directly_below_blocks = clean_directly_below_blocks

        return directly_below_blocks
    

    def boxes_directly_right(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get block right\n
        Get block right block, lowest distance, and intersecting with extension of block\n'''

        # get blocks right block
        right_blocks = [b for b in blocks if b.box.right > self.box.right and not b.box.is_inside_box(self.box) and b.box.intersects_box(self.box,extend_horizontal=True) and not b.box.intersects_box(self.box,extend_vertical=True)]

        # clean directly right blocks
        ## make sure no blocks are to the right of directly right blocks
        clean_directly_right_blocks = []
        for b1 in right_blocks:
            valid = True
            for b2 in right_blocks:
                if b2 == b1:
                    continue
                if (b1.box.intersects_box(b2.box,extend_horizontal=True,inside=True)) and b1.box.left > b2.box.left:
                    valid = False
                    break
            if valid:
                clean_directly_right_blocks.append(b1)
        directly_right_blocks = clean_directly_right_blocks
                
        return directly_right_blocks
    

    def boxes_directly_above(self,blocks:list["OCR_Tree"])->list["OCR_Tree"]:
        '''Get block above\n
        Get block above block, lowest distance, and intersecting with extension of block\n'''

        # extend block vertically
        block_extended = self.box.copy()
        block_extended.top = 0
        block_extended.bottom = 1000000

        # get blocks above block
        above_blocks = [b for b in blocks if b.box.bottom < self.box.bottom and not b.box.is_inside_box(self.box) and b.box.intersects_box(block_extended)]
        
        ## clean directly above blocks
        ### make sure no blocks are above directly above blocks
        clean_directly_above_blocks = []
        for b1 in above_blocks:
            valid = True
            for b2 in above_blocks:
                if b2 == b1:
                    continue
                if (b1.box.intersects_box(b2.box,extend_vertical=True,inside=True)) and b1.box.bottom < b2.box.bottom:
                    valid = False
                    break
            if valid:
                clean_directly_above_blocks.append(b1)
        directly_above_blocks = clean_directly_above_blocks

        return directly_above_blocks
    

    def change_ids(self,ids:dict,level:int=2,clean:bool=True):
        '''Change ids in ocr_results'''
        if self.level == level and self.id:
            if self.id in ids:
                self.id = ids[self.id]
            elif clean:
                self.id = None
        elif self.level < level:
            for child in self.children:
                child.change_ids(ids,level,clean)



    def join_trees(self,tree:'OCR_Tree'):
        '''Join trees of the same level'''
        if self.level == tree.level:
            # add tree childrens
            ## adapt children metadata to make sense in new tree (block_num,par_num)
            if self.children:
                last_child : OCR_Tree = self.children[-1]
                tree.update_children_metadata(reference_block=last_child.block_num,reference_par=last_child.par_num)
            self.children += tree.children
            # join boxes
            self.box.join(tree.box)


    def update_children_metadata(self,reference_block:int,reference_par:int):
        '''Update children metadata to make sense in new tree (block_num,par_num)'''
        self.block_num = reference_block
        self.par_num += reference_par
        for child in self.children:
            child.update_children_metadata(reference_block,reference_par)


    


