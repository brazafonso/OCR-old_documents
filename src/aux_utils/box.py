'''Module with box class, to represent a box container'''



class Box:
    left = None
    right = None
    top = None
    bottom = None
    width = None
    height = None

    def __init__(self, *args):
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
    
    def within_vertical_boxes(self,box):
        '''Check if boxes are within each other vertically'''
        if self.top >= box.top and self.bottom <= box.bottom:
            return True
        elif box.top >= self.top and box.bottom <= self.bottom:
            return True
        return False

    def within_horizontal_boxes(self,box):
        '''Check if boxes are within each other horizontally'''
        if self.left <= box.left and self.right >= box.right:
            return True
        elif box.left <= self.left and box.right >= self.right:
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
        intersect = self.intersects_box(area)
        inside = self.is_inside_box(area)
        if intersect and not inside:
            # Remove area from box
            ## area to the right
            if area.right > self.right:
                self.right = area.left
            ## area to the left
            if area.left < self.left:
                self.left = area.right
            ## area to the top
            if area.top > self.top:
                self.bottom = area.top
            ## area to the bottom
            if area.bottom < self.bottom:
                self.top = area.bottom
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
            if abs(1 - self.top/box.top) <= error_margin:
                return True
        elif orientation == 'vertical':
            if abs(1 - self.left/box.left) <= error_margin:
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