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
        self.box = None # info about box size and position on page
        self.text = None 
        self.conf = None
        self.id = None
        self.type = None # type of box (text, image ,delimiter, table, etc)
        self.children = []
        self.parent = None
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
            if json_list[i]['level'] == current_node.level + 1:
                current_node.add_child(node)
                node_stack.append(node)
            elif json_list[i]['level'] == current_node.level:
                node_stack.pop()
                current_node = node_stack[-1]
                current_node.add_child(node)
                node_stack.append(node)
            else:
                while json_list[i]['level'] != current_node.level + 1:
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
            if k != 'box':
                result[k].append(getattr(self,k))
            else:
                result[k].append(self.box.to_dict())
        for child in self.children:
            child.to_dict(result)
        return result

    
    def __str__(self):
        return f'OCR_Box(level={self.level},page_num={self.page_num},block_num={self.block_num},par_num={self.par_num},line_num={self.line_num},word_num={self.word_num},box={self.box},text={self.text},conf={self.conf},id={self.id})'

    def pretty_print(self,index:int=0):
        print('  '*index + str(self))
        for child in self.children:
            child.pretty_print(index+1)


    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def id_boxes(self,level:list[int]=[2],ids:dict=None):
        '''Id boxes in ocr_results'''
        if not ids:
            ids = {l:0 for l in level}
        if self.level in level:
            self.id = ids[self.level]
            ids[self.level] += 1
        for child in self.children:
            child.id_boxes(level,ids)


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
    
    def calculate_mean_height(self):
        '''Get mean height of group boxes'''
        line_sum = 0
        count = 1
        for child in self.children:
            line_sum += child.calculate_mean_height()
            count += 1
        return line_sum / count
    
    def is_text_size(self,text_size:float,mean_height:float=None,range:float=0.3):
        '''Check if text size is in range'''
        mean_height = mean_height
        if not mean_height:
            mean_height = self.get_mean_height()
        if mean_height >= text_size*(1-range) and mean_height <= text_size*(1+range):
            return True
        return False
    
    def is_empty(self,conf:int=0):
        '''Check if box is empty'''
        empty = re.match(r'^\s*$',self.text)
        i = 0
        while empty and i < len(self.children):
            empty = self.children[i].is_empty(conf)
            i += 1
        return empty
    
    def is_delimiter(self,conf:int=0):
        '''Check if box is delimiter'''
        if self.level == 2 and self.is_empty(conf):
            if self.box.width >= self.box.height*4 or self.box.height >= self.box.width*4:
                return True
        return False

    def get_delimiters(self,search_area:Box=None,orientation:str=None,conf:int=0):
        '''Get delimiters in ocr_results'''
        delimiters = []
        if self.is_delimiter(conf):
            valid = True
            if search_area and not self.box.is_inside_box(search_area):
                valid = False
            if orientation and self.box.get_box_orientation() != orientation:
                valid = False
            if valid:
                delimiters.append(self)
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
