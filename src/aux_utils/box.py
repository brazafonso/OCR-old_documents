'''Module with box class, to represent a box container'''



import math



class Box:
    left = None
    right = None
    top = None
    bottom = None
    width = None
    height = None

    def __init__(self, *args):
        '''Initialize Box object\n
        Available constructors:\n
        Box(left:int, right:int, top:int, bottom:int)\n
        Box(json_dict:dict)\n'''
        if len(args) == 1:
            self.load_json(args[0])
        else:
            self.init(*args)


    def init(self, left, right, top, bottom):
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.width = right - left
        self.height = bottom - top

    def load_json(self,json_dict:dict):
        self.left = json_dict['left']
        self.right = json_dict['right']
        self.top = json_dict['top']
        self.bottom = json_dict['bottom']
        self.width = json_dict['width']
        self.height = json_dict['height']

    def copy(self):
        return Box(self.left,self.right,self.top,self.bottom)

    def __str__(self):
        return f'left:{self.left} right:{self.right} top:{self.top} bottom:{self.bottom}'

    def to_json(self):
        return {
            'left':self.left,
            'right':self.right,
            'top':self.top,
            'bottom':self.bottom,
            'width':self.width,
            'height':self.height
        }
    
    def to_dict(self):
        return {
            'left':self.left,
            'right':self.right,
            'top':self.top,
            'bottom':self.bottom,
            'width':self.width,
            'height':self.height
        }
    
    def within_vertical_boxes(self,box,range=0):
        '''Check if boxes are within each other vertically, considering a range'''
        # avoid division by zero
        topmost = min(self.top,box.top)
        toplest = max(self.top,box.top)
        bottommost = max(self.bottom,box.bottom)
        bottomlest = min(self.bottom,box.bottom)

        # check if self is within box with range
        if (topmost == toplest or self.top <= box.top or abs(1 - toplest/topmost) <= range) and (bottommost == bottomlest or self.bottom >= box.bottom or abs(1 - bottomlest/bottommost) <= range):
            return True
        elif (topmost == toplest or box.top <= self.top or abs(1 - toplest/topmost) <= range) and (bottommost == bottomlest or box.bottom >= self.bottom or abs(1 - bottomlest/bottommost) <= range):
            return True
        return False
            

    def within_horizontal_boxes(self,box,range=0):
        '''Check if boxes are within each other horizontally, considering a range'''
        # avoid division by zero
        leftmost = min(self.left,box.left)
        leftlest = max(self.left,box.left)
        rightmost = max(self.right,box.right)
        rightlest = min(self.right,box.right)

        # check if self is within box with range
        if (leftmost == leftlest or self.left <= box.left or abs(1 - leftlest/leftmost) <= range) and (rightmost == rightlest or self.right >= box.right or abs(1 - rightlest/rightmost) <= range):
            return True
        elif (leftmost == leftlest or box.left <= self.left or abs(1 - leftlest/leftmost) <= range) and (rightmost == rightlest or box.right >= self.right or abs(1 - rightlest/rightmost) <= range):
            return True
        return False


    def same_level_box(self,box):
        '''Check if two boxes are in the same level (horizontal and/or vertical)'''
        if self.within_horizontal_boxes(box) or self.within_vertical_boxes(box):
            return True
        return False


    def is_inside_box(self,box):
        '''Check if box is inside container'''
        if self.left >= box.left and self.right <= box.right and self.top >= box.top and self.bottom <= box.bottom:
            return True
        return False


    def intersects_box(self,box,extend_vertical=False,extend_horizontal=False):
        '''Check if box intersects another box'''
        self_top = self.top
        self_bottom = self.bottom
        self_left = self.left
        self_right = self.right
        if extend_vertical:
            self_top = 0
            self_bottom = 100000
        if extend_horizontal:
            self_left = 0
            self_right = 100000
            
        intercept_vertical = (self_top <= box.top and self_bottom >= box.top) or (box.top <= self_top and box.bottom >= self_top)
        intercept_horizontal = (self_left <= box.right and self_right >= box.left) or (self_left <= box.right and self_right >= box.right)
        if intercept_horizontal and intercept_vertical:
            return True
        return False

    def intersect_area_box(self,box):
        '''Get intersect area box between two boxes'''
        area_box = Box(0,0,0,0)
        
        if self.left <= box.left:
            area_box.left = box.left
        else:
            area_box.left = self.left

        if self.right >= box.right:
            area_box.right = box.right
        else:
            area_box.right = self.right

        if self.top <= box.top:
            area_box.top = box.top
        else:
            area_box.top = self.top

        if self.bottom >= box.bottom:
            area_box.bottom = box.bottom
        else:
            area_box.bottom = self.bottom
        return area_box

    def remove_box_area(self,area):
        '''Remove area from box (only if intersect)'''
        if area:
            intersect = self.intersects_box(area)
            inside = self.is_inside_box(area)
            if intersect and not inside:
                above = area.top >= self.top
                to_left = area.left <= self.left

                # Remove area from box
                if not above and area.left <= self.left:
                    self.left = area.right
                elif not above and area.right >= self.right:
                    self.right = area.left
                elif above and area.bottom <= self.bottom:
                    self.top = area.bottom
                elif not above and area.top >= self.top:
                    self.bottom = area.top


                # Update width and height
                self.width = self.right - self.left
                self.height = self.bottom - self.top
        

    def box_is_smaller(self,box):
        '''Check if self is smaller than box'''
        if (self.right - self.left) * (self.bottom - self.top) < (box.right - box.left) * (box.bottom - box.top):
            return True
        return False
    

    def get_box_orientation(self):
        '''Get box orientation'''
        if self.width > self.height:
            return 'horizontal'
        elif self.width < self.height:
            return 'vertical'
        else:
            return 'square'
        

    def is_aligned(self,box:'Box',orientation='horizontal',error_margin=0.1):
        '''Check if boxes are aligned'''
        if orientation == 'horizontal':
            high = max(self.top,box.top)
            low = min(self.top,box.top)
            if low == high:
                return True
            if abs(1 - low/high) <= error_margin:
                return True
        elif orientation == 'vertical':
            high = max(self.left,box.left)
            low = min(self.left,box.left)
            if low == high:
                return True
            if abs(1 - low/high) <= error_margin:
                return True
        return False
    
    def join(self,box:'Box'):
        '''Join two boxes'''
        self.left = min(self.left,box.left)
        self.right = max(self.right,box.right)
        self.top = min(self.top,box.top)
        self.bottom = max(self.bottom,box.bottom)
        self.height = self.bottom - self.top
        self.width = self.right - self.left



    def blocks_directly_bellow(self,blocks:list["OCR_Box"]):
        '''Get block bellow\n
        Get block bellow block, lowest distance, and intersecting with extension of block\n'''

        # extend block vertically
        block_extended = self.copy()
        block_extended.top = 0
        block_extended.bottom = 1000000

        # get blocks bellow block
        bellow_blocks = [b for b in blocks if b.box.top > self.top and b.box.intersects_box(block_extended)]
        shortest_distance = None
        directly_bellow_blocks = []
        bellow_block = None

        # get block with shortest distance
        for b in bellow_blocks:
            distance = math.sqrt((self.left-b.box.left)**2 + (self.top-b.box.top)**2)
            if not shortest_distance or distance < shortest_distance:
                shortest_distance = distance
                bellow_block = b

        # directly bellow blocks is bellow block and verticaly aligned that are in bellow_blocks
        if bellow_block:
            directly_bellow_blocks = [b for b in bellow_blocks if b.box.within_vertical_boxes(bellow_block.box)]

        return directly_bellow_blocks
    

    def blocks_directly_right(self,blocks:list["OCR_Box"]):
        '''Get block right\n
        Get block right block, lowest distance, and intersecting with extension of block\n'''

        # extend block horizontally
        block_extended = self.copy()
        block_extended.left = 0
        block_extended.right = 1000000

        # get blocks right block
        right_blocks = [b for b in blocks if b.box.left > self.left and b.box.intersects_box(block_extended)]
        shortest_distance = None
        directly_right_blocks = []
        right_block = None

        # get block with shortest distance
        for b in right_blocks:
            distance = math.sqrt((self.left-b.box.left)**2 + (self.top-b.box.top)**2)
            if not shortest_distance or distance < shortest_distance:
                shortest_distance = distance
                right_block = b

        # directly right blocks is right block and horizontal aligned that are in right_blocks
        if right_block:
            directly_right_blocks = [b for b in right_blocks if b.box.within_horizontal_boxes(right_block.box)]

        return directly_right_blocks
    

    def distance_to(self,box:'Box'):
        '''Get distance to box'''
        return math.sqrt((self.left-box.left)**2 + (self.top-box.top)**2)
