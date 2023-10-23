import copy
import sys
from ocr_box_module.ocr_box import OCR_Box

class page_tree:
    '''Tree structure for pages composed of tesseract box elements\n
    Each node is a tesseract box element that is the leftmost in its height (from the top of the image)\n
    The right child of each node is the next node in the same height, and further to the right\n
    The left child of each node is a node with greater height.
    '''
    def __init__(self,data=None) -> None:
        self.data = data
        self.left_child = None
        self.right_child = None


    def insert(self,ocr_box:OCR_Box):
        '''Inserts a box element into the tree'''
        #print('inserting',box['text'])
        sys.setrecursionlimit(10000)
        if not self.data:
            self.data = ocr_box
            #print('1')
        else:
            # if box is the same height as node
            if self.data.box.top == ocr_box.box.top or (self.data.block_num == ocr_box.block_num and self.data.par_num == ocr_box.par_num and self.data.line_num == ocr_box.line_num):
                if self.data.box.left < ocr_box.box.left:
                    if self.right_child:
                        #print('2')
                        self.right_child.insert(ocr_box)
                    else:
                        #print('3')
                        self.right_child = page_tree(ocr_box)
                # swap node with new box
                else:
                    print('swapping',self.data.text,'with',ocr_box.text)
                    old_tree = self
                    self.left_child = old_tree.left_child
                    old_tree.left_child = None
                    self.right_child = old_tree
                    self.data = ocr_box
                    #print('4')
            # if box is greater height than node
            elif self.data.box.top < ocr_box.box.top:
                if self.left_child:
                    #print('5')
                    self.left_child.insert(ocr_box)
                else:
                    #print('6')
                    self.left_child = page_tree(ocr_box)
            # if box is less height than node
            else:
                #print('7')
                old_tree = self
                self.left_child = old_tree
                self.right_child = None
                self.data = ocr_box

    def pretty_print(self,indent=0):
        '''Prints the tree in a readable format'''
        if self.data:
            print(' '*indent,self.data.text)
        if self.right_child:
            self.right_child.pretty_print(indent+2)
        if self.left_child:
            self.left_child.pretty_print(indent+1)

    def to_list(self):
        '''Returns the tree as a list'''
        new_list = []
        if self.data:
            new_list = [self.data]
            if self.right_child:
                new_list += self.right_child.to_list()
            if self.left_child:
                new_list += self.left_child.to_list()
        return new_list
