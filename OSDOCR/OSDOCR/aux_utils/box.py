'''Module with box class, to represent a box container'''



import math
from typing import Union



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


    def init(self, left:int, right:int, top:int, bottom:int):
        self.left = int(left)
        self.right = int(right)
        self.top = int(top)
        self.bottom = int(bottom)
        self.width = self.right - self.left
        self.height = self.bottom - self.top

    def load_json(self,json_dict:dict):
        self.left = int(json_dict['left'])
        self.right = int(json_dict['right'])
        self.top = int(json_dict['top'])
        self.bottom = int(json_dict['bottom'])
        self.width = self.right - self.left
        self.height = self.bottom - self.top

    def __eq__(self, comparison: object) -> bool:
        '''Check if two boxes are equal (same dimensions)'''
        if isinstance(comparison,Box):
            return int(self.left) == int(comparison.left) and int(self.right) == int(comparison.right) \
                and int(self.top) == int(comparison.top) and int(self.bottom) == int(comparison.bottom)
        else:
            return False

    def copy(self):
        return Box(self.left,self.right,self.top,self.bottom)

    def __str__(self):
        return f'left:{self.left} right:{self.right} top:{self.top} bottom:{self.bottom} width:{self.width} height:{self.height}'
    
    def __dict__(self):
        return self.to_dict()

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
    

    def update(self, left:int=None, right:int=None, top:int=None, bottom:int=None,invert:bool=True):
        if left is not None:
            self.left = int(left)
        if right is not None:
            self.right = int(right)
        if top is not None:
            self.top = int(top)
        if bottom is not None:
            self.bottom = int(bottom)

        # fix inverted box
        if invert:
            if self.left > self.right:
                self.left, self.right = self.right, self.left
            if self.top > self.bottom:
                self.top, self.bottom = self.bottom, self.top
        # fix width and height so that they are valid
        else:
            if self.left > self.right:
                self.left = self.right
            if self.top > self.bottom:
                self.top = self.bottom

        self.width = self.right - self.left
        self.height = self.bottom - self.top


    def move(self, x:int=0, y:int=0):
        '''Move box'''
        if x:
            self.left += x
            self.right += x
        if y:
            self.top += y
            self.bottom += y
    
    def valid(self):
        '''Check if box is valid'''
        if self.left is None or self.right is None or self.top is None or self.bottom is None or \
            self.left>self.right or self.top>self.bottom:
            return False
        return True
    

    def area(self):
        return self.width * self.height
    
    def within_vertical_boxes(self,box: 'Box',range:float=0,only_self:bool=False):
        '''Check if boxes are within each other vertically, considering a range (0-1)'''
        
        # check if box is within self with range
        if (self.top - self.height*range <= box.top and self.bottom + self.height*range >= box.bottom):
            return True
        
        # check if self is within box with range
        if not only_self and (box.top - box.height*range <= self.top and box.bottom + box.height*range >= self.bottom):
            return True


        return False
            

    def within_horizontal_boxes(self, box: 'Box', range:float=0,only_self:bool=False):
        '''Check if boxes are within each other horizontally, considering a range (0-1)'''
        
        # check if box is within self with range
        if (self.left - self.width*range <= box.left and self.right + self.width*range >= box.right):
            return True
        
        # check if self is within box with range
        if not only_self and (box.left - box.width*range <= self.left and box.right + box.width*range >= self.right):
            return True

        return False


    def same_level_box(self,box:'Box'):
        '''Check if two boxes are in the same level (horizontal and/or vertical)'''
        if self.within_horizontal_boxes(box) or self.within_vertical_boxes(box):
            return True
        return False


    def is_inside_box(self,box:'Box'):
        '''Check if box is inside container'''
        if self.left >= box.left and self.right <= box.right and self.top >= box.top and self.bottom <= box.bottom:
            return True
        return False


    def intersects_box(self,box:'Box',extend_vertical:bool=False,extend_horizontal:bool=False,inside:bool=False):
        '''Check if box intersects another box'''
        self_box = self.copy()
        self_box:Box
        if extend_vertical:
            self_box.top = 0
            self_box.bottom = box.bottom + 1
        if extend_horizontal:
            self_box.left = 0
            self_box.right = box.right + 1
            
        intercept_vertical = extend_vertical or (self_box.top <= box.top and self_box.bottom >= box.top) \
                                or (box.top <= self_box.top and box.bottom >= self_box.top)
        
        intercept_horizontal = extend_horizontal or (self_box.left <= box.right and self_box.right >= box.left) \
                                or (self_box.left <= box.right and self_box.right >= box.right)
        
        if intercept_horizontal and intercept_vertical:
            return True
        
        if inside and (self_box.is_inside_box(box) or box.is_inside_box(self_box)):
            return True

        return False

    def intersect_area_box(self,box:'Box',extend_vertical:bool=False,extend_horizontal:bool=False)->Union['Box',None]:
        '''Get intersect area box between two boxes'''
        area_box = Box(0,0,0,0)

        self_box = self.copy()
        self_box:Box
        if extend_vertical:
            self_box.top = 0
            self_box.bottom = box.bottom + 1
        if extend_horizontal:
            self_box.left = 0
            self_box.right = box.right + 1

        intersects = self.intersects_box(box,extend_vertical=extend_vertical,
                                         extend_horizontal=extend_horizontal,inside=True)
        if not intersects:
            return area_box
        
        left = 0
        right = 0
        bottom = 0
        top = 0
        if self_box.left <= box.left:
            left = box.left
        else:
            left = self_box.left

        if self_box.right >= box.right:
            right = box.right
        else:
            right = self_box.right

        if self_box.top <= box.top:
            top = box.top
        else:
            top = self_box.top

        if self_box.bottom >= box.bottom:
            bottom = box.bottom
        else:
            bottom = self_box.bottom

        area_box.update(left=left,right=right,top=top,bottom=bottom)

        if not area_box.valid():
            return None
        

        return area_box

    def remove_box_area(self,area:'Box'):
        '''Remove area from box (only if intersect)'''
        if area:
            inside = self.is_inside_box(area)
            done = inside
            # While intersecting
            ## choose action (cut in direction) that removes the less area
            while not done:
                intersect = self.intersects_box(area)
                if intersect:
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


    

    def distance_to(self,box:'Box',border:str=None,range_x:Union[int,float]=0.3,range_y:Union[int,float]=0.3,range_type:str='relative'):
        '''Get distance to box
        
        Uses euclidean distance between center points of boxes
        
        If border arg is initialized, uses distance between borders instead of center points.
        Border arg can be one of: 'left','right','top','bottom','closest'

        If border arg is None, uses center points of boxes

        If border arg is 'closest', uses the closest border to the center point of box or closest border of box.
            * range_x and range_y can be used to specify the range when checking if boxes are within each other

        '''

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
        # search for closest distance
        ## simple naive approach
        elif border == 'closest':
            distance = None
            vertical_distance = None
            center_point = self.center_point()
            box_center_point = box.center_point()
            ## check if box is within range vertically
            if self.within_horizontal_boxes(box,range=range_x,range_type=range_type):
                # calculate vertical distance
                vertical_distance = min(abs(center_point[1] - box_center_point[1]),abs(self.bottom - box.top),abs(self.top - box.bottom))
                    
            horizontal_distance = None
            ## check if box is within range horizontally
            if self.within_vertical_boxes(box,range=range_y,range_type=range_type):
                # calculate horizontal distance
                horizontal_distance = min(abs(center_point[0] - box_center_point[0]),abs(self.right - box.left),abs(self.left - box.right))

            ## return closest distance
            distance = min(vertical_distance,horizontal_distance) if vertical_distance and horizontal_distance else [v for v in [vertical_distance,horizontal_distance] if v][0] if any([vertical_distance,horizontal_distance]) else None
            if distance:
                return distance
            else:
                self_point = self.center_point()
                box_point = box.center_point()
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
    
    def distance_to_point(self,x:int,y:int):
        '''Get distance to point'''
        center_x,center_y = self.center_point()
        dx = abs(center_x - x) - (self.width * 0.5)
        dy = abs(center_y - y) - (self.height * 0.5)
        return math.sqrt((dx * (dx > 0)) ** 2 + (dy * (dy > 0)) ** 2)
    
    def vertices(self):
        '''Get vertices of box.
        Order:
            - top left
            - top right
            - bottom right
            - bottom left
        '''
        return [(self.left,self.top),(self.right,self.top),(self.right,self.bottom),(self.left,self.bottom)]


    def closest_edge_point(self,x:int,y:int)->str:
        '''Get closest edge point to point. 
        Returns edge name (left, right, top, bottom)'''
        closest_edge = None
        closest_edge_dist = None
        # list of edges
        ## for each edge, list of vertex points and edge name
        left_edge = [(self.left,self.top),(self.left,self.bottom),'left']
        right_edge = [(self.right,self.top),(self.right,self.bottom),'right']
        top_edge = [(self.left,self.top),(self.right,self.top),'top']
        bottom_edge = [(self.left,self.bottom),(self.right,self.bottom),'bottom']
        edges = [left_edge,right_edge,top_edge,bottom_edge]
        for vertex_1,vertex_2,edge in edges:
            dist = None
            # check if point is within edge range
            ## horizontal
            if x >= vertex_1[0] and x <= vertex_2[0]:
                dist = abs(y - vertex_1[1])
            ## vertical
            elif y >= vertex_1[1] and y <= vertex_2[1]:
                dist = abs(x - vertex_1[0])
            ## distance to vertex of edge
            else:
                if x < vertex_1[0]:
                    if y < vertex_1[1]:
                        dist = math.sqrt((vertex_1[0] - x)**2 + (vertex_1[1] - y)**2)
                    else:
                        dist = math.sqrt((vertex_1[0] - x)**2 + (vertex_2[1] - y)**2)
                else:
                    if y < vertex_1[1]:
                        dist = math.sqrt((vertex_2[0] - x)**2 + (vertex_1[1] - y)**2)
                    else:
                        dist = math.sqrt((vertex_2[0] - x)**2 + (vertex_2[1] - y)**2)

            if dist and (not closest_edge_dist or dist < closest_edge_dist):
                closest_edge = edge
                closest_edge_dist = dist

        return closest_edge