import math
import os
import json
import re
from aux_utils.box import Box
'''Module to generalize OCR result into box object\n'''


class OCR_Box:
    '''Class to represent OCR results as a box object\n'''
    

    def __init__(self,*args):
        '''Initialize OCR_Box object\n
        Available constructors:\n
        OCR_Box(level:int, page_num:int, block_num:int, par_num:int, line_num:int, word_num:int, box:Box, text:str='',conf:int=-1,id=None,type:str=None)\n
        OCR_Box(json_list:list[dict])\n
        OCR_Box(json_file:str)\n'''
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
        '''Initialize OCR_Box object'''
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
            node = OCR_Box(json_list[i])
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
        '''Copy OCR_Box object'''
        return OCR_Box(self.level,self.page_num,self.block_num,self.par_num,self.line_num,self.word_num,self.box,self.text,self.conf,self.id,self.type)
            
        

    def __str__(self):
        return f'OCR_Box(level={self.level},page_num={self.page_num},block_num={self.block_num},par_num={self.par_num},line_num={self.line_num},word_num={self.word_num},box={self.box},text={self.text},conf={self.conf},id={self.id})'

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
    
    def get_boxes_level(self,level:int)->list['OCR_Box']:
        '''Get boxes with level in ocr_results'''
        group_boxes = []
        if self.level == level:
            group_boxes.append(self)
        else:
            for child in self.children:
                if child.level <= level:
                    group_boxes += child.get_boxes_level(level)
        return group_boxes
    
    def calculate_mean_height(self,level:int=5)->float:
        '''Get mean height of group boxes'''
        line_sum = 0
        count = 0
        if self.level == level:
            line_sum += self.box.height
            count += 1
        elif self.level < level:
            for child in self.children:
                line_sum += child.calculate_mean_height(level)
                count += 1
        return line_sum / count
    
    def is_text_size(self,text_size:float,mean_height:float=None,range:float=0.3):
        '''Check if text size is in range'''
        mean_height = mean_height
        if not mean_height:
            mean_height = self.calculate_mean_height()
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


    def get_boxes_in_area(self,area:Box,level:int=2)->list['OCR_Box']:
        '''Get boxes in area\n
        If level is -1, get all boxes in area'''
        boxes = []
        if area:
            if (level == -1 or self.level == level )and self.box.is_inside_box(area):
                boxes.append(self)
            elif self.level < level or level == -1:
                for child in self.children:
                    boxes += child.get_boxes_in_area(area,level)
        return boxes
    

    def type_color(self)->(int,int,int):
        '''Get block color, in rgb value, based on type
        
        Colors:
            - text: yellow
            - image: black
            - title: red
            - delimiter: blue
            - caption : white
            - other: green'''
        
        if self.type == 'text':
            return (255,255,0)
        elif self.type == 'image':
            return (0,0,0)
        elif self.type == 'title':
            return (255,0,0)
        elif self.type == 'delimiter':
            return (0,0,255)
        elif self.type == 'caption':
            return (255,255,255)
        else:
            return (0,255,0)
        

    def blocks_bellow(self,blocks:list["OCR_Box"])->list["OCR_Box"]:
        '''Get blocks bellow\n
        Get blocks bellow block, lowest distance, and intersecting with extension of block\n'''

        # extend block vertically
        block_extended = self.box.copy()
        block_extended.top = 0
        block_extended.bottom = 1000000

        # get blocks bellow block
        bellow_blocks = [b for b in blocks if b.box.top > self.box.top and b.box.intersects_box(block_extended)]
        return bellow_blocks
    
    def blocks_right(self,blocks:list["OCR_Box"])->list["OCR_Box"]:
        '''Get blocks right\n
        Get blocks right block, lowest distance, and intersecting with extension of block\n'''

        # extend block horizontally
        block_extended = self.box.copy()
        block_extended.left = 0
        block_extended.right = 1000000

        # get blocks right block
        right_blocks = [b for b in blocks if b.box.left > self.box.left and b.box.intersects_box(block_extended)]
        return right_blocks
    
    def blocks_above(self,blocks:list["OCR_Box"])->list["OCR_Box"]:
        '''Get blocks above\n
        Get blocks above block, lowest distance, and intersecting with extension of block\n'''

        # extend block vertically
        block_extended = self.box.copy()
        block_extended.top = 0
        block_extended.bottom = 1000000

        # get blocks above block
        above_blocks = [b for b in blocks if b.box.bottom < self.box.bottom and b.box.intersects_box(block_extended)]
        return above_blocks
    
    def blocks_left(self,blocks:list["OCR_Box"])->list["OCR_Box"]:
        '''Get blocks left\n
        Get blocks left block, lowest distance, and intersecting with extension of block\n'''

        # extend block horizontally
        block_extended = self.box.copy()
        block_extended.left = 0
        block_extended.right = 1000000

        # get blocks left block
        left_blocks = [b for b in blocks if b.box.right < self.box.right and b.box.intersects_box(block_extended)]
        return left_blocks



    def blocks_directly_bellow(self,blocks:list["OCR_Box"])->list["OCR_Box"]:
        '''Get block bellow\n
        Get block bellow block, lowest distance, and intersecting with extension of block\n'''

        # extend block vertically
        block_extended = self.box.copy()
        block_extended.top = 0
        block_extended.bottom = 1000000

        # get blocks bellow block
        bellow_blocks = [b for b in blocks if b.box.top > self.box.top and b.box.intersects_box(block_extended)]
        shortest_distance = None
        directly_bellow_blocks = []
        bellow_block = None

        # get block with shortest distance
        for b in bellow_blocks:
            distance = math.sqrt((self.box.left-b.box.left)**2 + (self.box.top-b.box.top)**2)
            if not shortest_distance or distance < shortest_distance:
                shortest_distance = distance
                bellow_block = b

        # directly bellow blocks is bellow block and verticaly aligned that are in bellow_blocks
        if bellow_block:
            directly_bellow_blocks = [b for b in bellow_blocks if b.box.within_vertical_boxes(bellow_block.box)]

        return directly_bellow_blocks
    

    def blocks_directly_right(self,blocks:list["OCR_Box"])->list["OCR_Box"]:
        '''Get block right\n
        Get block right block, lowest distance, and intersecting with extension of block\n'''

        # extend block horizontally
        block_extended = self.box.copy()
        block_extended.left = 0
        block_extended.right = 1000000

        # get blocks right block
        right_blocks = [b for b in blocks if b.box.left > self.box.left and b.box.intersects_box(block_extended)]
        shortest_distance = None
        directly_right_blocks = []
        right_block = None

        # get block with shortest distance
        for b in right_blocks:
            distance = math.sqrt((self.box.left-b.box.left)**2 + (self.box.top-b.box.top)**2)
            if not shortest_distance or distance < shortest_distance:
                shortest_distance = distance
                right_block = b

        # directly right blocks is right block and horizontal aligned that are in right_blocks
        if right_block:
            directly_right_blocks = [b for b in right_blocks if b.box.within_horizontal_boxes(right_block.box)]

        return directly_right_blocks
    

    def blocks_directly_above(self,blocks:list["OCR_Box"])->list["OCR_Box"]:
        '''Get block above\n
        Get block above block, lowest distance, and intersecting with extension of block\n'''

        # extend block vertically
        block_extended = self.box.copy()
        block_extended.top = 0
        block_extended.bottom = 1000000

        # get blocks above block
        above_blocks = [b for b in blocks if b.box.bottom < self.box.bottom and b.box.intersects_box(block_extended)]
        shortest_distance = None
        directly_above_blocks = []
        above_block = None

        # get block with shortest distance
        for b in above_blocks:
            distance = math.sqrt((self.box.left-b.box.left)**2 + (self.box.top-b.box.top)**2)
            if not shortest_distance or distance < shortest_distance:
                shortest_distance = distance
                above_block = b

        # directly above blocks is above block and verticaly aligned that are in above_blocks
        if above_block:
            directly_above_blocks = [b for b in above_blocks if b.box.within_vertical_boxes(above_block.box)]

        return directly_above_blocks
            


    


