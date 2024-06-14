'''Module for journal article output'''

import re
from OSDOCR.ocr_tree_module.ocr_tree_analyser import analyze_text
from OSDOCR.ocr_tree_module.ocr_tree import OCR_Tree
from OSDOCR.aux_utils.box import Box


class Article:
    '''Class that represents a journal article\n
    Stores the text of the article, its title, authors, etc.; as well as its bounding box'''



    def __init__(self,*args):
        '''Initialize Article object\n
        Available constructors:\n
        Article(ocr_tree:ocr_tree)\n
        Article(title:str,authors:list[str],abstract:str,body:str,bounding_box:Box)\n
        '''
        self.title = None
        self.subtitle = []
        self.authors = []
        self.abstract = None
        self.body = None
        self.bounding_box = None
        self.original_ocr_tree = None
        self.metadata = None
        self.sorted = False
        # single arg (ocr_tree)
        if isinstance(args[0],OCR_Tree):
            ocr_tree = [args[0]]
            args[0] = ocr_tree
            self.from_ocr_trees(*args)
        elif isinstance(args[0],list):
            self.from_ocr_trees(*args)
        # multiple args (title, authors, etc)
        else:
            self.init(*args)



    def from_ocr_trees(self,ocr_trees:list[OCR_Tree],conf:int=0):
        '''Initialize Article object from list of ocr_tree objects'''
        # create original ocr box
        self.original_ocr_tree = OCR_Tree(
            {'level':1,'page_num':0,'block_num':0,'par_num':0,'line_num':0,
             'word_num':0,'box':Box(0,0,0,0)}
             )
        self.original_ocr_tree.children = ocr_trees


        # analyze text
        text_analysis = analyze_text(self.original_ocr_tree)
        # print('article analysis',text_analysis)


        # get title
        ## biggest box before normal text
        potential_title_boxes = []
        abstract_boxes = []
        for ocr_tree in ocr_trees:
            if not ocr_tree.is_empty(conf=conf):
                if ocr_tree.text_is_title(text_analysis['normal_text_size'],conf=conf):
                    potential_title_boxes.append(ocr_tree)
                # break when normal text is found and there are potential title boxes
                elif ocr_tree.is_text_size(text_analysis['normal_text_size']) and potential_title_boxes:
                    break
                else:
                    abstract_boxes.append(ocr_tree)


        # print('potential title boxes',potential_title_boxes)
        if potential_title_boxes:
            ## get biggest box
            title_box = max(potential_title_boxes,key=lambda x: x.calculate_mean_height())
            # print('title box',title_box.to_text(),title_box.calculate_mean_height())
            self.title = title_box.to_text()
            ## get subtitle
            ## all other potential title boxes
            potential_title_boxes.remove(title_box)
            self.subtitle = [box.to_text() for box in potential_title_boxes]

        
        # abstract
        if abstract_boxes and self.title:
            self.abstract = ' '.join([box.to_text() for box in abstract_boxes])

        # authors
        ## TODO

        # body
        ## TODO fix
        body_boxes = []
        if self.title:
            body_boxes = [b for b in ocr_trees if b != title_box]
        else:
            body_boxes = ocr_trees
        self.body = ' '.join([box.to_text() for box in body_boxes])




    def init(self,title:str,authors:list[str],abstract:str,body:str,bounding_box:Box):
        '''Initialize Article object from title, authors, abstract, body and bounding box'''
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.body = body
        self.bounding_box = bounding_box



    def pretty_print(self):
        '''Prints article in a pretty way'''
        text = ''
        text += f'''TITLE: {self.title}
----------------------------------'''
        text += f'''
----------------------------------
        AUTHORS: {", ".join(self.authors)}
----------------------------------'''
        text += f'''
----------------------------------
        ABSTRACT: 
        {self.abstract}
----------------------------------'''
        text += f'''
----------------------------------
        BODY: 
{self.body}

----------------------------------'''
        return text
    
    def __str__(self):
        return f'Article(title={self.title},authors={self.authors},bounding_box={self.bounding_box})'
    
    def to_md(self):
        '''Returns article in markdown format'''
        text = ''
        clean_title = 'Default Title'
        if self.title:
            clean_title = re.sub(r'\s\s+', ' ', self.title)
        text += f'''# {clean_title}
        '''
        text += f'''
## Authors
        {", ".join(self.authors)}
        '''
        text += f'''
## Abstract
        {self.abstract}
        '''
        text += f'''
## Body
        {self.body}
        '''
        return text
    

    def to_txt(self):
        '''Returns article in txt format'''
        text = f'{self.title}\n{self.body}\n'
        return text