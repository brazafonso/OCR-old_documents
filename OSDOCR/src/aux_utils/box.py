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
    
    def valid(self):
        '''Check if box is valid'''
        if self.left is None or self.right is None or self.top is None or self.bottom is None or self.left>self.right or self.top>self.bottom:
            return False
        return True
    
    def within_vertical_boxes(self,box,range=0):
        '''Check if boxes are within each other vertically, considering a range'''
        # avoid division by zero
        topmost = min(self.top,box.top)
        topleast = max(self.top,box.top)
        bottommost = max(self.bottom,box.bottom)
        bottomlest = min(self.bottom,box.bottom)

        # avoid division by zero
        top_ratio = abs(topleast / topmost - 1) if topmost != 0 else abs(topleast / 0.1 - 1)
        bottom_ratio = abs(bottomlest / bottommost - 1) if bottommost != 0 else abs(bottomlest / 0.1 - 1)

        # check if self is within box with range
        if (topmost == topleast or self.top <= box.top or top_ratio <= range) and (bottommost == bottomlest or self.bottom >= box.bottom or bottom_ratio <= range):
            return True

        # check if box is within self with range
        elif (topmost == topleast or box.top <= self.top or top_ratio<= range) and (bottommost == bottomlest or box.bottom >= self.bottom or bottom_ratio <= range):
            return True
        return False
            

    def within_horizontal_boxes(self, box, range=0):
        '''Check if boxes are within each other horizontally, considering a range'''
        # avoid division by zero
        leftmost = min(self.left, box.left)
        leftleast = max(self.left, box.left)
        rightmost = max(self.right, box.right)
        rightleast = min(self.right, box.right)

        
        # avoid division by zero
        left_ratio = abs(leftleast / leftmost - 1) if leftmost != 0 else abs(leftleast / 0.1 - 1)
        right_ratio = abs(rightleast / rightmost - 1) if rightmost != 0 else abs(rightleast / 0.1 - 1)

        # check if box is within self with range
        if (self.left <= box.left or left_ratio <= range) and (self.right >= box.right or right_ratio <= range):
            return True

        # check if self is within box with range
        if (box.left <= self.left or left_ratio <= range) and (box.right >= self.right or right_ratio <= range):
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


    def intersects_box(self,box,extend_vertical:bool=False,extend_horizontal:bool=False,inside:bool=False):
        '''Check if box intersects another box'''
        self_box = self.copy()
        if extend_vertical:
            self_box.top = 0
            self_box.bottom = 100000
        if extend_horizontal:
            self_box.left = 0
            self_box.right = 100000
            
        intercept_vertical = (self_box.top <= box.top and self_box.bottom >= box.top) or (box.top <= self_box.top and box.bottom >= self_box.top)
        intercept_horizontal = (self_box.left <= box.right and self_box.right >= box.left) or (self_box.left <= box.right and self_box.right >= box.right)
        if intercept_horizontal and intercept_vertical:
            return True
        
        if inside and (self_box.is_inside_box(box) or box.is_inside_box(self_box)):
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

        if not area_box.valid():
            return None

        return area_box

    def remove_box_area(self,area):
        '''Remove area from box (only if intersect)'''
        if area:
            inside = self.is_inside_box(area)
            done = False
            while not done:
                intersect = self.intersects_box(area)
                if intersect and not inside:
                    above = area.bottom < self.bottom
                    to_left = area.right < self.right
                    to_right = area.left > self.left
                    below = area.top > self.top

                    # if more than one condition is true, choose the one that removes less area
                    combinations = {
                        'above' : (above,area.bottom-self.top),
                        'to_left' : (to_left,area.right-self.left),
                        'to_right' : (to_right,self.right-area.left),
                        'below' : (below,self.bottom-area.top)
                    }
                    combinations = {k:v for k,v in combinations.items() if v[0]}
                    combinations = sorted(combinations.items(),key=lambda x:x[1][1])[0]
                    for c in ['above','to_left','to_right','below']:
                        if c in combinations:
                            above = c == 'above'
                            to_left = c == 'to_left'
                            to_right = c == 'to_right'
                            below = c == 'below'
                            break



                    # Remove area from box
                    if to_right:
                        self.right = area.left-1
                    elif to_left:
                        self.left = area.right+1
                    elif above:
                        self.top = area.bottom+1
                    elif below:
                        self.bottom = area.top-1
                    else:
                        done = True

                else:
                    done = True

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


    

    def distance_to(self,box:'Box',border:str=None):
        '''Get distance to box
        
        Uses euclidean distance between center points of boxes
        
        If border arg is initialized, uses distance between borders instead of center points'''

        if border and border in ['left','right','top','bottom']:
            if border == 'left':
                self_point = self.left_middle_point()
                box_point = box.right_middle_point()
            elif border == 'right':
                self_point = self.right_middle_point()
                box_point = box.left_middle_point()
            elif border == 'top':
                self_point = self.top_middle_point()
                box_point = box.bottom_middle_point()
            elif border == 'bottom':
                self_point = self.bottom_middle_point()
                box_point = box.top_middle_point()
        else:
            self_point = self.center_point()
            box_point = box.center_point()
        return math.sqrt((self_point[0]-box_point[0])**2 + (self_point[1]-box_point[1])**2)
    
    def center_point(self):
        '''Get center point of box'''
        return (self.left+self.width/2,self.top+self.height/2)
    
    def top_middle_point(self):
        '''Get top middle point of box'''
        return (self.left+self.width/2,self.top)
    
    def bottom_middle_point(self):
        '''Get bottom middle point of box'''
        return (self.left+self.width/2,self.bottom)
    
    def left_middle_point(self):
        '''Get left middle point of box'''
        return (self.left,self.top+self.height/2)
    
    def right_middle_point(self):
        '''Get right middle point of box'''
        return (self.right,self.top+self.height/2)
