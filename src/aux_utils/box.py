'''Module with box class, to represent a box container'''



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


    def intersects_box(self,box):
        '''Check if box intersects another box'''
        intercept_vertical = (self.top <= box.top and self.bottom >= box.top) or (box.top <= self.top and box.bottom >= self.top)
        intercept_horizontal = (self.left <= box.right and self.right >= box.left) or (self.left <= box.right and self.right >= box.right)
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