'''OCR Editor  - GUI'''

import os
import random
import shutil
import time
import cv2
import pyperclip
import matplotlib
import matplotlib.patches
import matplotlib.pyplot as plt
import PySimpleGUI as sg
import matplotlib.text
import matplotlib.typing
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle, Rectangle
from matplotlib.lines import Line2D
from matplotlib.animation import FuncAnimation
from document_image_utils.image import segment_document_delimiters
from OSDOCR.aux_utils import consts
from OSDOCR.aux_utils.misc import *
from OSDOCR.output_module.journal.article import Article
from .layouts.ocr_editor_layout import *
from ..aux_utils.utils import *
from OSDOCR.parse_args import preprocessing_methods,process_args
from OSDOCR.ocr_tree_module.ocr_tree import *
from OSDOCR.pipeline import run_target_image
from OSDOCR.ocr_tree_module.ocr_tree_fix import find_text_titles, split_block,\
                                                split_whitespaces,block_bound_box_fix,\
                                                text_bound_box_fix,remove_empty_boxes,\
                                                unite_blocks,bound_box_fix_image,delimiters_fix
from OSDOCR.ocr_tree_module.ocr_tree_analyser import categorize_boxes, extract_articles,\
                                                     order_ocr_tree
from .configuration_gui import run_config_gui,read_ocr_editor_configs_file

file_path = os.path.dirname(os.path.realpath(__file__))

# allow matplotlib to use tkinter
matplotlib.use('TkAgg')

# global variables
window = None
last_window_size = None
block_filter = None
config = {}
## variables for canvas
image_plot = None
current_image_path = None
current_image = None
figure_canvas_agg = None
figure = None
animation = None
default_edge_color = None
## variables for ocr results
bounding_boxes = {}
current_ocr_results = None
current_ocr_results_path = None
cache_ocr_results = []
current_cache_ocr_results_index = -1
ocr_results_articles = {}
## actions
'''
Possible actions:
    - move
    - expand
    - select
    - split_block
    - split_image
'''
current_action = None
current_action_start = None
last_key = None
last_mouse_position = (0,0)
highlighted_blocks = []
focused_block = None
last_activity_time = time.time()
## constants
ppi = 300   # default pixels per inch
max_block_dist = 10 # max distance from a block to a click
vertex_radius = 5
edge_thickness = 2
id_text_size = 10
SYMBOL_UP =    '▲'
SYMBOL_DOWN =  '▼'


################################################
###########                   ##################
###########   GUI FUNCTIONS   ##################
###########                   ##################
################################################


def update_config_dependent_variables():
    '''Update config dependent variables'''
    global config,ppi,vertex_radius,edge_thickness,id_text_size
    changed = False
    try:
        if config['base']['ppi'] != ppi:
            changed = True
            ppi = config['base']['ppi']
    except:
        pass
    try:
        if config['base']['vertex_radius'] != vertex_radius:
            changed = True
            vertex_radius = config['base']['vertex_radius']
    except:
        pass
    try:
        if config['base']['edge_thickness'] != edge_thickness:
            changed = True
            edge_thickness = config['base']['edge_thickness']
    except:
        pass
    try:
        if config['base']['id_text_size'] != id_text_size:
            changed = True
            id_text_size = config['base']['id_text_size']
    except:
        pass

    return changed



def choose_window_image_input(values:dict):
    global figure,current_ocr_results,current_ocr_results_path,bounding_boxes,animation\
            ,ocr_results_articles, ppi, current_image_path,window,config
    if current_image_path:
        # reset variables
        figure = None
        current_ocr_results = None
        current_ocr_results_path = None
        bounding_boxes = {}
        ocr_results_articles = {}
        ppi = config['base']['ppi']
        animation.pause()
        clean_ocr_result_cache()
    
    update_canvas_image(window,values)
    print('Chose target image')


def refresh_layout():
    '''Refresh layout so sizes are updated'''
    global window
    print('Refresh layout')
    window_size = window.size
    print('Window size:',window_size)
    # update body columns
    ## ratios of | 1/8 | 4/8 | 3/8 |
    ratio_1 = 1/10
    # left side bar is collapsible, so ratio is dynamic
    ratio_2 = 6/10 if window['collapse_body_left_side_bar'].visible else 7/10
    ratio_3 = 3/10
    window['body_left_side_bar'].Widget.canvas.configure({'width':window_size[0]*ratio_1,'height':None})
    window['body_canvas'].Widget.canvas.configure({'width':window_size[0]*ratio_2,'height':None})
    window['body_right_side_bar'].Widget.canvas.configure({'width':window_size[0]*ratio_3,'height':None})

    window.refresh()


def add_ocr_result_cache(ocr_result:OCR_Tree):
    '''Add ocr result to cache'''
    global cache_ocr_results,current_cache_ocr_results_index,config
    print('Add ocr result to cache',current_cache_ocr_results_index,'len:',len(cache_ocr_results))
    if len(cache_ocr_results) >= config['base']['cache_size'] and len(cache_ocr_results) > 0:
        cache_ocr_results.pop(0)

    if current_cache_ocr_results_index+1 > len(cache_ocr_results)-1:
        cache_ocr_results.append(ocr_result.copy())
    else:
        cache_ocr_results[current_cache_ocr_results_index + 1] = ocr_result.copy()
    current_cache_ocr_results_index += 1
    # clean old cache
    clean_ocr_result_cache(current_cache_ocr_results_index+1)


def pop_ocr_result_cache():
    '''Pop ocr result from cache'''
    global cache_ocr_results
    if len(cache_ocr_results) > 0:
        cache_ocr_results.pop(0)

def clean_ocr_result_cache(position:int=0):
    '''Clean ocr result cache from position and up'''
    global cache_ocr_results,current_cache_ocr_results_index
    if len(cache_ocr_results) > 0 and position < len(cache_ocr_results):
        cache_ocr_results = cache_ocr_results[:position]
        current_cache_ocr_results_index = position - 1


def undo_operation():
    '''Undo last opeartion'''
    global current_cache_ocr_results_index,current_ocr_results,window
    print('Undo operation | index:',current_cache_ocr_results_index,'len:',len(cache_ocr_results))
    if len(cache_ocr_results) > 0 and current_cache_ocr_results_index > 0 and \
        current_cache_ocr_results_index < len(cache_ocr_results):
        
        current_cache_ocr_results_index -= 1
        current_ocr_results = cache_ocr_results[current_cache_ocr_results_index].copy()
        refresh_ocr_results()

def redo_operation():
    '''Redo last opeartion'''
    global current_cache_ocr_results_index,current_ocr_results,window
    print('Redo operation')
    if current_cache_ocr_results_index < len(cache_ocr_results)-1:
        current_cache_ocr_results_index += 1
        current_ocr_results = cache_ocr_results[current_cache_ocr_results_index].copy()
        refresh_ocr_results()


def update_canvas_column(window:sg.Window):
    '''Update canvas column. Uses TKinter canvas for performance'''
    global figure_canvas_agg
    print('Update canvas column')
    canvas = window['body_canvas'].Widget.canvas
    w,h = figure_canvas_agg.get_width_height()
    # add some padding
    w += 50
    h += 50
    canvas.config(scrollregion=(0,0,w,h)) 

def update_canvas(window:sg.Window,figure):
    '''Update canvas'''
    global figure_canvas_agg,animation
    if figure:
        bounding_boxes = get_bounding_boxes()
        if bounding_boxes:
            animation = FuncAnimation(figure, update, frames=60, blit=True,
                                      interval=1000/60,repeat=True)
        # update canvas
        canvas = window['canvas']
        ## use TKinter canvas
        tkcanvas = canvas.TKCanvas
        figure_canvas_agg = FigureCanvasTkAgg(figure, tkcanvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)



def sidebar_update_block_info():
    global window,highlighted_blocks,config

    if highlighted_blocks:
        block = highlighted_blocks[-1]['block']
        block:OCR_Tree
        # update block info
        ## id
        window['input_block_id'].update(block.id)
        ## coordinates
        left = int(block.box.left)
        top = int(block.box.top)
        right = int(block.box.right)
        bottom = int(block.box.bottom)
        window['text_block_coords'].update(f'({left},{top}) - ({right},{bottom})')
        window['text_block_level'].update(highlighted_blocks[-1]['z'])
        ## type
        block_type = block.type if block.type else ''
        window['list_block_type'].update(block_type)
        ## text
        text_delimiters = {3: '\n'}
        text_confidence = config['base']['text_confidence']
        block_text = block.to_text(conf=text_confidence,text_delimiters=text_delimiters).strip()
        window['input_block_text'].update(block_text)
    else:
        # clear block info
        window['input_block_id'].update('')
        window['text_block_coords'].update('')
        window['text_block_level'].update('')
        window['list_block_type'].update('')
        window['input_block_text'].update('')


################################################
###########                   ##################
###########  CANVAS FUNCTIONS ##################
###########                   ##################
################################################


def clear_canvas():
    '''Clear canvas'''
    global image_plot,figure_canvas_agg,animation
    print('Clear canvas')
    try:
        if animation:
            animation.event_source.stop()
        if figure_canvas_agg:
            figure_canvas_agg.get_tk_widget().forget()
    except Exception as e:
        print(e)

def refresh_canvas(refresh_image:bool=True,refresh_ocr_results:bool=True):
    '''Redraws canvas with current ocr results'''
    global window,current_image_path,current_image,current_ocr_results,image_plot
    if current_image_path or current_ocr_results:
        # draw image
        if current_image_path and refresh_image:
            if not current_image:
                current_image = cv2.imread(current_image_path)
                current_image = cv2.cvtColor(current_image, cv2.COLOR_BGR2RGB)
            clear_canvas()
            # create new plot
            image_plot = create_plot(current_image)
            # update canvas
            update_canvas(window,figure)

        # draw ocr results
        if current_ocr_results and refresh_ocr_results:
            draw_ocr_results(current_ocr_results,window)

        # warn column of content change
        update_canvas_column(window)


def select_action_assets():
    '''Create assets for select action. Transparent square representing selection area.'''
    global current_action,current_action_start,highlighted_blocks,image_plot
    assets = []
    if current_action == 'select':
        start_x,start_y = current_action_start
        x,y = last_mouse_position
        if x is not None and y is not None:
            width = x - start_x
            height = y - start_y
            edge_color = (0.0157,0.3882,0.5019,1)
            selection_square = Rectangle((start_x,start_y),width,height,linewidth=3,
                                         edgecolor=edge_color,facecolor=(0,0,1,0.1),)
            image_plot.add_patch(selection_square)
            assets.append(selection_square)
    return assets

def split_action_assets():
    '''Create assets for split action'''
    global current_action,last_mouse_position,highlighted_blocks,\
        default_edge_color,image_plot,current_image_path
    assets = []
    if current_action == 'split_block':
        x,y = last_mouse_position
        if x is not None and y is not None:
            block = highlighted_blocks[-1]['block']
            orientation,line = split_line(x,y,block)
            if orientation and line:
                x_data = [line.left, line.right]
                y_data = [line.top, line.bottom]
                line_asset = Line2D(x_data,y_data,linewidth=2, color=default_edge_color,
                                    marker='o', markersize=5, markerfacecolor=default_edge_color, 
                                    markeredgewidth=2, markeredgecolor='black',linestyle='--')

                assets.append(line_asset)
                image_plot.add_line(line_asset)
    elif current_action == 'split_image' and current_image_path:
        x,y = last_mouse_position
        if x is not None and y is not None:
            img = cv2.imread(current_image_path)
            widht,height = img.shape[1],img.shape[0]
            img_box = Box(0, widht, 0, height)
            orientation,line = split_line(x,y,img_box)
            if orientation and line:
                x_data = [line.left, line.right]
                y_data = [line.top, line.bottom]
                line_asset = Line2D(x_data,y_data,linewidth=2, color=default_edge_color,
                                    marker='o', markersize=5, markerfacecolor=default_edge_color, 
                                    markeredgewidth=2, markeredgecolor='black',linestyle='--')

                assets.append(line_asset)
                image_plot.add_line(line_asset)
    return assets

def update(frame):
    '''Update canvas'''
    global current_action,last_mouse_position,highlighted_blocks,block_filter
    assets = []
    bounding_boxes = get_bounding_boxes()
    if bounding_boxes:
        # update position of boxes and id texts
        for block in bounding_boxes.values():
            box = block['box']
            # if filter is set, check if block is valid
            if block_filter:
                if not block_filter(block['block']):
                    continue
            # update rectangle
            rect = block['rectangle']
            rect.set_xy((box.left, box.top))
            rect.set_width(box.width)
            rect.set_height(box.height)
            # update vertices
            vertices_circles = block['vertices_circles']
            vertices = box.vertices()
            for i,vertex in enumerate(vertices):
                vertices_circles[i].set_center(vertex)
            # update id text
            id_text = block['id_text']
            id_text_x = box.left+15
            id_text_y = box.top+30
            id_text.set_x(id_text_x)
            id_text.set_y(id_text_y)

            assets.append(rect)
            assets.extend(vertices_circles)
            assets.append(id_text)

        # case of split block action
        if current_action == 'split_block':
            split_assets = split_action_assets()
            assets.extend(split_assets)

        # case of split image action
        if current_action == 'split_image' and current_image_path:
            split_assets = split_action_assets()
            assets.extend(split_assets)

        # case of select block action
        if current_action == 'select':
            select_assets = select_action_assets()
            assets.extend(select_assets)

    return assets

def create_plot(image:Union[str,cv2.typing.MatLike]):
    '''Create plot with image'''
    global ppi,figure
    # read image
    if isinstance(image,str):
        image = cv2.imread(image)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # change image size
    sizes = image.shape
    figure = plt.figure(figsize=(sizes[1]/ppi,sizes[0]/ppi))
    ax = plt.Axes(figure, [0., 0., 1., 1.])
    ax.set_axis_off()
    figure.add_axes(ax)
    # connect events
    # fig.canvas.mpl_connect('draw_event', canvas_on_draw)
    figure.canvas.mpl_connect('button_press_event', canvas_on_button_press)
    figure.canvas.mpl_connect('key_press_event', canvas_on_key_press)
    figure.canvas.mpl_connect('key_release_event', canvas_on_key_release)
    figure.canvas.mpl_connect('button_release_event', canvas_on_button_release)
    figure.canvas.mpl_connect('motion_notify_event', canvas_on_mouse_move)

    ax.imshow(image)
    figure.canvas.draw_idle()

    return ax


def update_canvas_image(window:sg.Window,values:dict):
    '''Update canvas image element. Creates new plot with image'''
    global image_plot,figure,figure_canvas_agg,current_image_path,ppi,\
        default_edge_color,config,current_image
    if values['target_input']:
        path = values['target_input']
        if config['base']['use_pipeline_results']:
            results_path = f'{consts.result_path}/{path_to_id(path)}'
        else:
            results_path = path
        metadata = get_target_metadata(path)
        browse_file_initial_folder = None

        if not metadata:
            target_img_path = path
            browse_file_initial_folder = os.path.dirname(path)
        else:
            target_img_path = metadata['target_path']
            browse_file_initial_folder = f'{results_path}/processed'
        
        current_image_path = target_img_path
        current_image = cv2.imread(target_img_path)
        current_image = cv2.cvtColor(current_image, cv2.COLOR_BGR2RGB)

        # update default edge color for ocr results
        default_edge_color = get_average_inverse_color(current_image)
        color = default_edge_color * 255
        color = (int(color[0]),int(color[1]),int(color[2]))
        window['text_default_color'].update(text_color = rgb_to_hex(color),
                                            background_color = rgb_to_hex(color))

        clear_canvas()
        # create new plot
        image_plot = create_plot(current_image)
        # update canvas
        update_canvas(window,figure)

        # update browse location for 'ocr_results_input'
        window['browse_file'].InitialFolder = browse_file_initial_folder
        # update browse location for 'target_input'
        window['browse_image'].InitialFolder = os.path.dirname(path)

def update_canvas_ocr_results(window:sg.Window,values:dict):
    '''Update canvas ocr_results element. Creates new plot with ocr_results'''
    global current_ocr_results,current_ocr_results_path,current_image_path,config
    if values['ocr_results_input'] and current_image_path:
        current_ocr_results_path = values['ocr_results_input']

        if not os.path.exists(current_ocr_results_path):
            # message to OCR image first
            sg.popup('Please rerun OCR on target image first')
            return
        
        # read ocr results
        current_ocr_results = OCR_Tree(current_ocr_results_path,
                                       config['base']['text_confidence'])
        ## draw ocr results in canvas
        draw_ocr_results(current_ocr_results,window)
        # update browse location for 'ocr_results_input'
        window['ocr_results_input'].InitialFolder = os.path.dirname(current_ocr_results_path)


def create_ocr_block_assets(block:OCR_Tree,override:bool=True):
    '''Create ocr block assets and add them to canvas figure'''
    global image_plot,bounding_boxes,default_edge_color,vertex_radius,\
        edge_thickness,id_text_size
    # check if block id exists
    block_id = block.id
    if block_id in bounding_boxes and not override:
        # if exists, change to biggest id
        block.id = max(bounding_boxes.keys())+1
    # bounding box
    box = block.box
    left = box.left
    top = box.top
    right = box.right
    bottom = box.bottom
    # draw bounding box (rectangle)
    bounding_box = Rectangle((left,top),right-left,bottom-top,linewidth=edge_thickness,
                             edgecolor=default_edge_color,facecolor='none')
    image_plot.add_patch(bounding_box)
    vertices = box.vertices()
    vertices_circles = []
    # draw vertices
    for vertex in vertices:
        x,y = vertex
        vertex_circle = Circle((x,y),radius=vertex_radius,edgecolor='b',facecolor='b')
        image_plot.add_patch(vertex_circle)
        vertices_circles.append(vertex_circle)
    # draw id text in top left corner of bounding box
    id_text = matplotlib.text.Text(left+15,top+30,block.id,color='r',
                fontproperties=matplotlib.font_manager.FontProperties(size=id_text_size))
    image_plot.add_artist(id_text)

    # save bounding box in dictionary
    bounding_boxes[block.id] = {
        'rectangle':bounding_box,
        'block':block,
        'box':box,
        'id_text' : id_text,
        'id' : block.id,
        'vertices_circles' : vertices_circles,
        'click_count' : 0,
        'z' : 1
    }


    

def draw_ocr_results(ocr_results:OCR_Tree,window:sg.Window):
    '''Draw ocr results in canvas'''
    global image_plot,figure,figure_canvas_agg,ppi,current_image_path,\
        bounding_boxes,default_edge_color,current_image
    # get new plot to draw ocr results
    image_plot = create_plot(current_image)

    # id blocks and get them
    ocr_results.id_boxes(level=[2],override=False)
    blocks = ocr_results.get_boxes_level(level=2)

    bounding_boxes = {}
    # draw ocr results
    for block in blocks:
        create_ocr_block_assets(block,override=False)
        
    # clear canvas
    clear_canvas()
    # # update canvas
    update_canvas(window,figure)


def unique_article_color(used_colors:list=[]):
    '''Get unique article color'''
    unique_color = False
    color = None
    while not unique_color:
        color = (random.randint(0,255)/255,random.randint(0,255)/255,random.randint(0,255)/255)
        if color not in used_colors:
            unique_color = True
    return color

def unique_article_id(used_ids:list=[]):
    '''Get unique article id'''
    unique_id = False
    id = 0
    while not unique_id:
        if id not in used_ids:
            unique_id = True
        else:
            id += 1
    return id

def draw_articles():
    '''Draw articles in ocr editor'''
    global ocr_results_articles,bounding_boxes,default_edge_color,window
    # reset color of all blocks
    toggle_ocr_results_block_type(bounding_boxes,default_edge_color,
                                  window['checkbox_toggle_block_type'].get())
    # update color of blocks in articles
    for i,article in ocr_results_articles.items():
        article_color = article['color']
        for block in article['article']:
            block:OCR_Tree
            bb_block = bounding_boxes[block.id]
            rect = bb_block['rectangle']
            # update edge color
            rect.set_edgecolor(article_color)

    window['checkbox_toggle_articles'].update(True)


def refresh_articles():
    '''Refresh articles in ocr editor. Remove articles that have no blocks'''
    global ocr_results_articles
    if ocr_results_articles:
        og_len = len(ocr_results_articles)
        ocr_results_articles = {k:v for k,v in ocr_results_articles.items() if len(v['article']) > 0}
        new_len = len(ocr_results_articles)
        if new_len != og_len:
            update_sidebar_articles()


def highlight_block(block:dict):
    '''Add block to highlighted blocks. If already highlighted, bring it to front of stack.'''
    global highlighted_blocks
    highlighted_blocks_ids = [x['id'] for x in highlighted_blocks]
    # update rectangle to have transparent red facecolor
    rectangle = block['rectangle']
    rectangle.set_facecolor((1,0,0,0.1))
    if block['id'] not in highlighted_blocks_ids:
        block['click_count'] = 1
        block['z'] = 2
    else:
        block['click_count'] += 1
        index = highlighted_blocks_ids.index(block['id'])
        highlighted_blocks.pop(index)

    highlighted_blocks.append(block)
        


def canvas_on_button_press(event):
    '''Handle mouse click events'''
    global current_action,current_action_start,bounding_boxes,\
        highlighted_blocks,last_activity_time,focused_block,window
    print(f'click {event}')
    # left click
    if event.button == 1:
        # calculate closest block
        click_x = event.xdata
        click_y = event.ydata
        if not current_action or current_action not in ['split_block','split_image']:
            current_action_start = (click_x,click_y)
            block_id,_ = closest_block(click_x,click_y)
            if block_id is not None:
                # print(f'closest block {block_id}')
                block = bounding_boxes[block_id]
                # highlight block
                highlight_block(block)

                focused_block = block
                block_box = block['box']
                block_box:Box
                distance = block_box.distance_to_point(click_x,click_y)
                # check what action to activate
                ## move, if distance is 0 and not close enough to any of the vertices
                ## expand otherwhise

                ### check if move
                if distance == 0:
                    # check distance to vertices
                    vertices = block_box.vertices()
                    v_distances = enumerate([math.sqrt((x-click_x)**2+(y-click_y)**2) for x,y in vertices])
                    v_distance = min(v_distances,key=lambda x: x[1])
                    if v_distance[1] > 5:
                        current_action = 'move'
                    else:
                        current_action = 'expand'
                
                ### expand
                else:
                    current_action = 'expand'

                # update block info in sidebar

            else:
                current_action = 'select'

            sidebar_update_block_info()

        elif current_action == 'split_block':
            # if first click (no current_action_start)
            split_ocr_block(int(click_x),int(click_y))
            current_action = None
            add_ocr_result_cache(current_ocr_results)

        elif current_action == 'split_image':
            # create event for main window
            ## bug - if creating popup windows from handler, blocks the main window
            window.write_event_value('method_split_image',(click_x,click_y))
            
            

    # middle click
    elif event.button == 2:
        ## create new block
        click_x = event.xdata
        click_y = event.ydata
        create_new_ocr_block(x=click_x,y=click_y)
        add_ocr_result_cache(current_ocr_results)

    last_activity_time = time.time()





def canvas_on_button_release(event):
    '''Mouse release event handler'''
    global current_action,current_action_start,current_ocr_results
    print(f'release {event}')
    release_x = event.xdata
    release_y = event.ydata
    
    # select action
    if current_action == 'select' and \
        (current_action_start[0] != release_x or current_action_start[1] != release_y):
        current_action = None
        # select area
        select_area_left = min(current_action_start[0],release_x)
        select_area_top = min(current_action_start[1],release_y)
        select_area_right = max(current_action_start[0],release_x)
        select_area_bottom = max(current_action_start[1],release_y)
        select_area = Box({'left':select_area_left,
                           'right':select_area_right,
                           'top':select_area_top,
                           'bottom':select_area_bottom})
        # get blocks inside select area
        blocks = current_ocr_results.get_boxes_in_area(select_area,level=2)

        # highlight blocks
        for block in blocks:
            block = bounding_boxes[block.id]
            highlight_block(block)
        # update sidebar block info
        sidebar_update_block_info()

    # if click on a block and highlighted_blocks and click without moving, disselect block
    ## if click outside of block and highlighted_blocks and click without moving, disselect blocks
    elif highlighted_blocks and \
        (current_action_start[0] == release_x and current_action_start[1] == release_y):

        block_id,_ = closest_block(release_x,release_y)
        if block_id is not None:
            block = bounding_boxes[block_id]
            block_box = block['block'].box
            block_box:Box
            if block_box.distance_to_point(release_x,release_y) == 0 and block['click_count'] > 1:
                highlighted_blocks.remove(block)
                block['rectangle'].set_facecolor((1,1,1,0))
                # update block info in sidebar
                sidebar_update_block_info()
        else:
            reset_highlighted_blocks()

    elif highlighted_blocks and \
        (current_action_start[0] != release_x or current_action_start[1] != release_y):

        if current_action in ['move','expand']:
            add_ocr_result_cache(current_ocr_results)
            print(highlighted_blocks[-1]['block'].min_left())


    current_action = None

def canvas_on_mouse_move(event):
    '''Mouse move event handler'''
    global current_action,current_ocr_results,last_mouse_position,\
        bounding_boxes,highlighted_blocks,image_plot,last_activity_time,window

    # check if mouse is within interaction range of any block
    ## used to update mouse cursor
    try:
        block_id,_ = closest_block(event.xdata,event.ydata)
    except:
        block_id = None
    if block_id is not None:
        # interaction range cursor
        window.set_cursor('fleur')
    else:
        # default cursor
        window.set_cursor('left_ptr')



    if current_action and highlighted_blocks and last_mouse_position:
        if current_action == 'move':
            # calculate new position
            ## start position
            last_x = last_mouse_position[0]
            last_y = last_mouse_position[1]
            ## mouse position
            new_x = event.xdata
            new_y = event.ydata
            # print(f'mouse move {last_x},{last_y} -> {new_x},{new_y}')
            ## distance moved
            move_x = new_x - last_x
            move_y = new_y - last_y
            if move_x or move_y:
                for highlighted_block in highlighted_blocks:
                    # update box
                    block = highlighted_block['block']
                    block.update_position(top=move_y,left=move_x)
                    bounding_boxes[highlighted_block['id']]['box'] = block.box

        elif current_action == 'expand':
            # calculate new dimensions
            ## start position
            last_x = last_mouse_position[0]
            last_y = last_mouse_position[1]
            ## mouse position
            new_x = event.xdata
            new_y = event.ydata
            ## check which vertex is being moved (closest vertex)
            block = highlighted_blocks[-1]['block']
            block:OCR_Tree
            box = block.box
            vertices = box.vertices()
            distances = [(v_i,math.sqrt((x-last_x)**2+(y-last_y)**2)) for v_i,(x,y) in enumerate(vertices)]
            closest_vertex = min(distances,key=lambda x: x[1])
            v_i = closest_vertex[0]
            
            dx = new_x - last_x
            dy = new_y - last_y
            if dx:
                # left vertices update left position
                if v_i in [0,3]:
                    block.update_size(left=dx)
                else:
                    block.update_size(right=dx)

            if dy:
                # top vertices update top position
                if v_i in [0,1]:
                    block.update_size(top=dy)
                else:
                    block.update_size(bottom=dy)

                # update box
                bounding_boxes[highlighted_blocks[-1]['id']]['box'] = block.box
                # print(f'moved {move_x},{move_y} ! {box}')

        sidebar_update_block_info()

    last_mouse_position = (event.xdata,event.ydata)
    last_activity_time = time.time()


def canvas_on_key_press(event):
    ''' keyboard shortcuts '''
    global last_key,ppi,highlighted_blocks,current_action_start,\
            last_mouse_position,last_activity_time,\
            focused_block,current_ocr_results
    print(f'key {event.key}')
    if event.key == 'ctrl++':
        zoom_canvas(factor=-30)
    elif event.key == 'ctrl+-':
        zoom_canvas(factor=30)
    elif event.key == 'ctrl+z' and last_key == 'ctrl+shift':
        redo_operation()
        sidebar_update_block_info()
    elif event.key == 'ctrl+z':
        undo_operation()
        sidebar_update_block_info()
    elif str(event.key).isdigit():
        if len(highlighted_blocks) > 0:
            # update block id
            target_block = highlighted_blocks[-1]
            new_id = int(event.key)
            ## check if continous id update
            if focused_block['id'] == target_block['id']:
                diff_time = time.time() - last_activity_time
                if str(last_key).isdigit():
                    # if less than 0.5 seconds between updates, append number
                    if  diff_time < 0.5:
                        new_id = int(f'{target_block["id"]}{new_id}')
                else:
                    new_id = target_block['id']
            
            change_block_id(target_block['id'],int(new_id))
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)

    last_key = event.key
    last_activity_time = time.time()


def canvas_on_key_release(event):
    return


def destroy_canvas():
    """
    Destroys the canvas by removing the image plot and forgetting the figure canvas aggregate.
    """
    global image_plot,figure_canvas_agg
    if image_plot is not None:
        image_plot.remove()
        image_plot = None
    if figure_canvas_agg is not None:
        figure_canvas_agg.get_tk_widget().forget()
        figure_canvas_agg = None

def zoom_canvas(factor:int=1):
    '''Zoom canvas, altering ppi value by factor'''
    global ppi,current_ocr_results
    ppi += factor
    # refresh canvas
    refresh_image = True if not current_ocr_results else False
    refresh_ocr_results = True if current_ocr_results else False 
    refresh_canvas(refresh_image=refresh_image,refresh_ocr_results=refresh_ocr_results)


def reset_highlighted_blocks():
    '''Reset highlighted blocks'''
    global highlighted_blocks,focused_block
    for b in highlighted_blocks:
        rectangle = b['rectangle']
        rectangle.set_facecolor((1,1,1,0))
        # reset click count
        b['click_count'] = 0
        # b['z'] = 1
    highlighted_blocks = []
    focused_block = None


def reset_ocr_results(window:sg.Window):
    '''Reset ocr results'''
    global current_ocr_results,highlighted_blocks,current_action,config
    print('Reset ocr results')
    if current_ocr_results and current_ocr_results_path:
        # reload ocr results
        current_ocr_results = OCR_Tree(current_ocr_results_path,
                                       config['base']['text_confidence'])
        # reset variables
        reset_highlighted_blocks()
        current_action = None
        # draw ocr results in canvas
        draw_ocr_results(current_ocr_results,window)


def toggle_ocr_results_block_type(bounding_boxes:dict,default_color:str='#283b5b',toogle:bool=False):
    '''Change color of bounding boxes based on block type'''
    global window

    for b in bounding_boxes.values():
        rectangle = b['rectangle']
        block = b['block']
        block:OCR_Tree
        block_color = default_color
        if toogle and block.type:
            block_color = block.type_color(normalize=True,rgb=True)
        
        rectangle.set_edgecolor(block_color)

    window['checkbox_toggle_block_type'].update(toogle)



def send_blocks_to_back(boxes:list):
    '''Send highlighted blocks to back. Decreases z value'''
    for b in boxes:
        b['z'] -= 1
        # decrease gamma of rectangle edges
        rectangle = b['rectangle']
        color = rectangle.get_edgecolor()
        z = b['z']
        gamma = max(1-0.1*abs(1-z),0.1)
        rectangle.set_edgecolor((color[0],color[1],color[2],gamma))


def send_blocks_to_front(boxes:list):
    '''Send highlighted blocks to front. Increases z value'''
    for b in boxes:
        b['z'] += 1
        # decrease gamma of rectangle edges
        rectangle = b['rectangle']
        color = rectangle.get_edgecolor()
        z = b['z'] if b['z'] <= 1 else 1
        gamma = max(1-0.1*abs(1-z),0.1)
        rectangle.set_edgecolor((color[0],color[1],color[2],gamma))


def reset_blocks_z(boxes:list):
    '''Reset z value of blocks'''
    for b in boxes:
        b['z'] = 1
        # reset gamma of rectangle edges
        rectangle = b['rectangle']
        color = rectangle.get_edgecolor()
        rectangle.set_edgecolor((color[0],color[1],color[2],1))


def highlight_article(id:int):
    '''Highlight blocks of an article'''
    global ocr_results_articles,bounding_boxes
    print(f'Highlight article {id}')
    if id in ocr_results_articles:
        # reset highlighted blocks
        reset_highlighted_blocks()

        for block in ocr_results_articles[id]['article']:
            if block.id in bounding_boxes:
                # update highlighted block
                b = bounding_boxes[block.id]
                highlight_block(b)


################################################
###########                   ##################
###########   DATA FUNCTIONS  ##################
###########                   ##################
################################################


def get_bounding_boxes()->dict:
    '''Get bounding boxes'''
    global bounding_boxes,block_filter
    return_boxes = {}
    if bounding_boxes:
        for k,block in bounding_boxes.items():
            if block_filter is None or block_filter(block['block']):
                return_boxes[k] = block

    return return_boxes


def refresh_ocr_results():
    '''Refresh ocr results and bounding boxes'''
    global current_ocr_results,bounding_boxes,window,\
        default_edge_color,ocr_results_articles
    if current_ocr_results:
        # reset bounding boxes
        bounding_boxes = {}
        # reset articles
        ocr_results_articles = {}
        # reset highlighted blocks
        reset_highlighted_blocks()
        blocks = current_ocr_results.get_boxes_level(level=2)
        for block in blocks:
            create_ocr_block_assets(block,override=False)

        toggle_ocr_results_block_type(bounding_boxes=bounding_boxes,
                                      default_color=default_edge_color,
                                      toogle=window['checkbox_toggle_block_type'].get())


def update_sidebar_articles():
    '''Update sidebar articles information'''
    global window,ocr_results_articles

    data = []

    # create buttons for each article
    for k in ocr_results_articles:
        data += [f'{k}']

    window['table_articles'].update(values=data)


def closest_block(click_x,click_y)->Union[int,float]:
    '''Get closest block to click. Returns block id'''
    global max_block_dist
    block_id = None
    block_dist = None
    bounding_boxes = get_bounding_boxes()

    if bounding_boxes:
        # calculate distances
        calculate_distances = np.vectorize(lambda x: {
            'distance':x['box'].distance_to_point(click_x,click_y),
            'id':x['id'],
            'z' : x['z']
            })
        distances = calculate_distances(list(bounding_boxes.values()))
        # get closest
        c_block = sorted(distances,key=lambda x: x['distance'])
        ## choose the one with greatest z value
        min_dist = c_block[0]['distance']
        same_dist_blocks = [x for x in c_block if x['distance'] == min_dist]
        c_block = sorted(same_dist_blocks,key=lambda x: x['z'])[-1]
        c_block_id = c_block['id']
        c_block_dist = c_block['distance']
        # print(f'closest block {c_block_id} distance {c_block_dist}')
        # check if distance is less than max_block_dist
        if c_block_dist <= max_block_dist:
            block_id = c_block_id
            block_dist = c_block_dist
    return block_id,block_dist


def create_new_ocr_block(x:int=None,y:int=None):
    '''Create new ocr block. 
    If x and y are not None, create new block at that point. 
    Else, create new block at middle of canvas'''
    global current_ocr_results,current_image_path,figure,\
        default_edge_color,image_plot,animation
    
    if not current_image_path:
        return

    if x is None and y is None:
        # create new block at middle of canvas
        points = image_plot.get_window_extent().get_points()
        w = points[1][0] - points[0][0]
        h = points[1][1] - points[0][1]
        x = int(w/2)
        y = int(h/2)
    
    # create new ocr block
    ## get last id
    last_id = 0
    if current_ocr_results is not None:
        last_id = max(current_ocr_results.get_boxes_level(level=2),key=lambda b: b.id).id
    else:
        # create new ocr results
        ## also needs to resume animation
        animation.resume()
        last_id = -1
        img = cv2.imread(current_image_path)
        current_ocr_results = OCR_Tree({
            'level':0,
            'box':Box({
                'left':0,
                'top':0,
                'right':img.shape[1],
                'bottom':img.shape[0]
            }),
        })
        current_ocr_results.add_child(OCR_Tree({
            'level':1,
            'box':Box({
                'left':0,
                'top':0,
                'right':img.shape[1],
                'bottom':img.shape[0]
            }),
        }))

    new_id = last_id + 1
    new_block = OCR_Tree({
        'level':2,
        'id':new_id,
        'box':Box({
            'left':x,
            'top':y,
            'right':x+50,
            'bottom':y+50}),
    })

    # add new block
    ## ocr results
    page = current_ocr_results.get_boxes_level(level=1)[-1]
    page.add_child(new_block)
    ## bounding boxes
    create_ocr_block_assets(new_block,override=False)


def save_ocr_results(path:str=None,save_as_copy:bool=False):
    '''Save ocr results'''
    global current_ocr_results,current_ocr_results_path,current_image_path
    if current_ocr_results:
        save_path = path if path else current_ocr_results_path if current_ocr_results_path else current_image_path
        # copy ocr results
        if save_as_copy:
            valid_name = False
            id = 0
            base_path = save_path
            while not valid_name:
                if id == 0:
                    save_path = f'{base_path}_copy.json'
                else:
                    save_path = f'{base_path}_copy_{id}.json'
                if not os.path.exists(save_path):
                    valid_name = True
                    
                id += 1

        current_ocr_results.save_json(save_path)


def save_ocr_block_changes(values:dict):
    '''Save changes to current highlighted block. 
    The coordinates will be divided equally within the block.
    Confidence of words will be set to 100.'''
    global current_ocr_results,highlighted_blocks,config
    if current_ocr_results and highlighted_blocks:
        target_block = highlighted_blocks[-1]
        block = target_block['block']
        block:OCR_Tree
        rectangle = target_block['rectangle']
        # get new info from frame 'frame_block_info'
        ## block type ('list_block_type')
        block_type = values['list_block_type']
        ## block text ('input_block_text')
        block_text = values['input_block_text']
        ## block id ('input_block_id')
        block_id = values['input_block_id']
        ### turn block text into OCR Tree
        #### count number of paragraphs in line, to be able to divide coordinates equally
        pars = [par for par in block_text.split('\n\n') if par.strip()]
        for i,par in enumerate(pars):
            par_lines = par.split('\n')
            j = 0
            while j < len(par_lines):
                par_l = par_lines[j]
                if not par_l.strip():
                    par_lines.pop(j)
                else:
                    j += 1
            pars[i] = par_lines

        #### create OCR Trees
        par_height = int(block.box.height / len(pars))
        new_children = []
        ##### par level
        for i,par in enumerate(pars):
            par_children = []
            par_top = block.box.top + par_height * i
            par_left = block.box.left
            par_right = block.box.right
            par_bottom = par_top + par_height

            ##### line level
            for j,line in enumerate(par):
                line_height = int(par_height / len(par))
                line_top = par_top
                line_left = par_left
                line_right = par_right
                line_bottom = line_top + line_height
                line_tree = OCR_Tree({'level':4,
                                      'box':{'left':line_left,'top':line_top,
                                             'right':line_right,'bottom':line_bottom},
                                      'par_num':i,'line_num':j})
                line_words = [w for w in line.split(' ') if w.strip()]

                ##### word level
                for m,word in enumerate(line_words):
                    word_width = int(par_right - par_left) // len(line_words)
                    word_top = line_top
                    word_left = line_left + word_width * m
                    word_right = word_left + word_width
                    word_bottom = line_bottom
                    word_tree = OCR_Tree({'level':5,
                                          'box':{'left':word_left,'top':word_top,
                                                 'right':word_right,'bottom':word_bottom},
                                          'text':word,'conf':100,'par_num':i,
                                          'line_num':j,'word_num':m})
                    line_tree.add_child(word_tree)

                par_children.append(line_tree)

            if par_children:
                par_tree = OCR_Tree({'level':3,
                                     'box':{'left':par_left,'top':par_top,
                                            'right':par_right,'bottom':par_bottom},
                                            'children':par_children})
                new_children.append(par_tree)

        # change block children if text changed
        updated_block = OCR_Tree({'level':2,'box':block.box,'children':new_children})
        # text_confidence = config['base']['text_confidence'] 
        if updated_block.to_text().strip() != block.to_text().strip():
            block.children = new_children

        # change block type
        if block_type and block_type != block.type:
            block.type = block_type
            ## change color of rectangle if type color is toogled
            if values['checkbox_toggle_block_type']:
                color = block.type_color(normalize=True,rgb=True)
                rectangle.set_edgecolor(color)

        # change block id
        if block_id and block_id.isdigit() and block_id != block.id:
            change_block_id(block.id,int(block_id))

        add_ocr_result_cache(current_ocr_results)
        sidebar_update_block_info()


def delete_ocr_block():
    '''Delete highlighted ocr block'''
    global highlighted_blocks,current_ocr_results,bounding_boxes
    if highlighted_blocks:
        while highlighted_blocks:
            block = highlighted_blocks[0]
            ## remove block from ocr_results
            current_ocr_results.remove_box_id(block['id'])
            ## remove block from bounding_boxes
            del bounding_boxes[block['id']]
            ## remove block from highlighted_blocks
            highlighted_blocks.remove(block)

                
def remove_empty_blocks_method():
    '''Remove empty blocks from ocr_results'''
    global current_ocr_results
    if current_ocr_results:
        tree = current_ocr_results.copy()
        tree = remove_empty_boxes(tree,text_confidence=config['base']['text_confidence'],
                                  find_delimiters=False,find_images=False)
        # check changes
        blocks = current_ocr_results.get_boxes_level(level=2)
        # remove blocks that are not in remaining_blocks
        for block in blocks:
            if tree.get_box_id(block.id) is None:
                current_ocr_results.remove_box_id(block.id)
                del bounding_boxes[block.id]

        refresh_highlighted_blocks()


def apply_ocr_block():
    '''Apply OCR on highlighted ocr block'''
    global highlighted_blocks,current_image_path,config
    if highlighted_blocks:
        print('Apply OCR on highlighted ocr block')

        image = cv2.imread(current_image_path)
        block = highlighted_blocks[-1]
        ocr_block = block['block']
        ocr_block:OCR_Tree
        box = ocr_block.box.copy()

        # fix box if invalida coordinates
        if box.left < 0:
            box.left = 0
        if box.top < 0:
            box.top = 0
        if box.right > image.shape[1]:
            box.right = image.shape[1]
        if box.bottom > image.shape[0]:
            box.bottom = image.shape[0]

        # cut part of image
        left = int(box.left)
        top = int(box.top)
        right = int(box.right)
        bottom = int(box.bottom)
        image = image[top:bottom,left:right]

        # add some padding
        padding = 20
        avg_color = np.average(image,axis=(0,1))
        image = cv2.copyMakeBorder(image,padding,padding,padding,padding,
                                   cv2.BORDER_CONSTANT,value=avg_color)
        
        # save tmp image
        tmp_dir = consts.ocr_editor_tmp_path
        os.makedirs(tmp_dir,exist_ok=True)
        tmp_path = f'{tmp_dir}/tmp.png'
        cv2.imwrite(tmp_path,image)
        # create args for pipeline function
        ## skip methods
        skip_methods = preprocessing_methods.copy()
        skip_methods.remove('image_preprocess')
        if config['ocr_pipeline']['fix_rotation']  != 'none':
            skip_methods.remove('auto_rotate')
        if config['ocr_pipeline']['fix_illumination']:
            skip_methods.remove('light_correction')
        if config['ocr_pipeline']['upscaling_image'] != 'none':
            skip_methods.remove('image_upscaling')
        if config['ocr_pipeline']['denoise_image'] != 'none':
            skip_methods.remove('noise_removal')
        if config['ocr_pipeline']['binarize'] != 'none':
            skip_methods.remove('binarize_image')

        args = process_args()
        args.tesseract_config = config['ocr_pipeline']['tesseract_config']
        args.skip_method =  skip_methods
        args.binarize_image = [config['ocr_pipeline']['binarize']]
        args.logs = True
        # run ocr
        run_target_image(tmp_path,results_path=tmp_dir,args=args)
        # load ocr results
        ocr_results = OCR_Tree(f'{tmp_dir}/ocr_results.json',
                                       config['base']['text_confidence'])
        new_box = ocr_results.get_boxes_level(0)[0].box
        ## scale dimensions, OCR results may not align with ocr block size
        scale_height = box.height/new_box.height
        scale_width = box.width/new_box.width
        ocr_results.scale_dimensions(scale_width,scale_height)
        ## move ocr results to position of ocr block
        move_top = box.top - new_box.top
        move_left = box.left - new_box.left
        ocr_results.update_position(move_top,move_left)
        new_children = ocr_results.get_boxes_level(3)
        ocr_block.children = new_children
        # # remove tmp dir
        # shutil.rmtree(tmp_dir)


def copy_block_text():
    '''Copy highlighted ocr block text to clipboard'''
    global highlighted_blocks,config
    if highlighted_blocks:
        block = highlighted_blocks[-1]
        ocr_block = block['block']
        ocr_block:OCR_Tree
        text = ocr_block.to_text(conf=config['base']['text_confidence'])
        pyperclip.copy(text)
        


def join_ocr_blocks():
    '''Join highlighted ocr blocks'''
    global highlighted_blocks,bounding_boxes,current_ocr_results

    if not highlighted_blocks:
        return
    
    blocks = highlighted_blocks.copy()
    # sort blocks by highest
    blocks.sort(key=lambda b:b['block'].box.top)
    blocks_tree = [b['block'] for b in blocks]
    while len(blocks) > 1:
        first = blocks[0]['block']
        first_block = blocks[0]
        second = blocks[1]['block']
        second_block = blocks[1]
        # horizontal or vertical depend on which block is on the right
        orientation = 'horizontal' if second in first.boxes_directly_right(blocks_tree) \
                        or first in second.boxes_directly_right(blocks_tree) else 'vertical'
        # if horizontal, sort by left
        if orientation == 'horizontal':
            if first.box.left > second.box.left:
                first,second = second,first
                first_block,second_block = second_block,first_block
        first.join_trees(second,orientation=orientation)
        # remove second block
        ## remove second block from ocr_results
        current_ocr_results.remove_box_id(second.id)
        ## remove second block from bounding_boxes
        del bounding_boxes[second.id]
        ## remove second block from highlighted_blocks
        highlighted_blocks.remove(second_block)
        ## remove second block from blocks
        blocks.remove(second_block)



def split_line(x:int,y:int,block:Union[OCR_Tree,Box])->Union[str,Box]:
    '''Gets split line for ocr block. Returns orientation and split line box.
    
    Returns:
        Orientation: 'horizontal' or 'vertical'
        Box: Split line box
    '''
    # get split line
    split_delimiter = None
    orientation = None
    box = block.box if isinstance(block,OCR_Tree) else block
    ## get closest edge to mouse click
    closest_edge = box.closest_edge_point(x,y)
    ### horizontal split
    if closest_edge in ['left','right']:
        orientation = 'horizontal'
        left = box.left
        right = box.right
        top = y if y <= box.bottom and y >= box.top else box.top if y < box.top else box.bottom
        bottom = top + 1
        split_delimiter = Box({'left': left,'right': right,'top': top,'bottom': bottom})
    ### vertical split
    elif closest_edge in ['top','bottom']:
        orientation = 'vertical'
        top = box.top
        bottom = box.bottom
        left = x if x <= box.right and x >= box.left else box.left if x < box.left else box.right
        right = left + 1
        split_delimiter = Box({'left': left,'right': right,'top': top,'bottom': bottom})

    return orientation,split_delimiter


def split_ocr_block(x:int,y:int):
    '''Split ocr block. x,y is position of mouse click and will be used to calculate split line.'''
    global highlighted_blocks,current_ocr_results,config
    if highlighted_blocks and len(highlighted_blocks) == 1:
        block = highlighted_blocks[0]['block']
        block:OCR_Tree
        orientation,split_delimiter = split_line(x,y,block)
        # split block
        if split_delimiter:
            print(f'Splitting block: {block.id}')
            text_confidence = config['base']['text_confidence']
            blocks = split_block(block,split_delimiter,orientation=orientation,
                                 conf=text_confidence,keep_all=True,debug=True)
            if len(blocks) > 1:
                new_block = blocks[1]
                # add new block
                ## get last id
                last_id = max(current_ocr_results.get_boxes_level(level=2),key=lambda b: b.id).id + 1
                new_block.id = last_id
                ## add new block to ocr_results
                page = current_ocr_results.get_boxes_level(1)[0]
                page.children.append(new_block)
                ## create assets
                create_ocr_block_assets(new_block)

            # update sidebar block info
            sidebar_update_block_info()


def split_image_method(x:int,y:int):
    '''Method to split image and respective ocr results (if any). 
    Creates new image and ocr result files and resets ocr editor canvas and cache.'''
    global current_ocr_results,current_ocr_results_path,current_image_path,\
        window,default_edge_color,config
    ocr_results_path = None
    image_path = None
    if current_image_path:
        # split image
        ## get image size
        img = cv2.imread(current_image_path)
        height,width,_ = img.shape
        image_box = Box({'left':0,'right':width,'top':0,'bottom':height})
        orientation,split_delimiter = split_line(x,y,image_box)
        if split_delimiter:
            popup_location = window.mouse_location()
            image_area = None
            # cut image
            if orientation == 'horizontal':
                option = popup_window(title='Area to keep',message='Choose area to keep',
                                      options=('top','bottom'),location=popup_location,modal=True)
                if option == 'top':
                    img = img[0:split_delimiter.top,0:width]
                    image_area = Box({'left':0,'right':width,
                                      'top':0,'bottom':split_delimiter.top})
                elif option == 'bottom':
                    img = img[split_delimiter.bottom:height,0:width]
                    image_area = Box({'left':0,'right':width,
                                      'top':split_delimiter.bottom,'bottom':height})
                    
            elif orientation == 'vertical':
                option = popup_window(title='Area to keep',message='Choose area to keep',
                                      options=('left','right'),location=popup_location,modal=True) 
                if option == 'left':
                    img = img[0:height,0:split_delimiter.left]
                    image_area = Box({'left':0,'right':split_delimiter.left,
                                      'top':0,'bottom':height})
                elif option == 'right':
                    img = img[0:height,split_delimiter.right:width]
                    image_area = Box({'left':split_delimiter.right,'right':width,
                                      'top':0,'bottom':height})
            
            # save image
            image_name = os.path.splitext(os.path.basename(current_image_path))[0]
            image_path = os.path.join(os.path.dirname(current_image_path),f'{image_name}_split.png')
            id = 0
            while os.path.exists(image_path):
                id += 1
                image_path = os.path.join(os.path.dirname(current_image_path),
                                          f'{image_name}_split_{id}.png')
            cv2.imwrite(image_path,img)

            # split ocr results
            if current_ocr_results and image_area:
                image_area:Box
                tree = current_ocr_results.get_boxes_level(0)[0].copy()
                page = tree.get_boxes_level(1)[0]
                # split ocr results
                ## keep only boxes in image area
                if not config['methods']['image_split_keep_all']:
                    blocks = page.get_boxes_in_area(image_area,level=2)
                    # clear page
                    page.children = []
                    page.update_box(left=image_area.left,top=image_area.top,
                                    right=image_area.right,bottom=image_area.bottom)
                    # add blocks in image area to page
                    for block in blocks:
                        page.add_child(block.copy())
                ## keep all boxes, cutting those that intersect image area
                else:
                    blocks = [b for b in page.get_boxes_level(2) if b.box.intersects_box(image_area,inside=True)]
                    # clear page
                    page.children = []
                    page.update_box(left=image_area.left,top=image_area.top,
                                    right=image_area.right,bottom=image_area.bottom)
                    # cut boxes that intersect image area
                    for block in blocks:
                        if not block.box.is_inside_box(image_area):
                            intersect_edge = image_area.closest_edge_point(*block.box.center_point())
                            cut_orientation = None
                            if intersect_edge == 'left':
                                cut_line = Box({'left':image_area.left-1,'right':image_area.left,
                                                'top':image_area.top,'bottom':image_area.bottom})
                                cut_orientation = 'vertical'
                            elif intersect_edge == 'right':
                                cut_line = Box({'left':image_area.right,'right':image_area.right+1,
                                                'top':image_area.top,'bottom':image_area.bottom})
                                cut_orientation = 'vertical'
                            elif intersect_edge == 'top':
                                cut_line = Box({'left':image_area.left,'right':image_area.right,
                                                'top':image_area.top+1,'bottom':image_area.top})
                                cut_orientation = 'horizontal'
                            elif intersect_edge == 'bottom':
                                cut_line = Box({'left':image_area.left,'right':image_area.right,
                                                'top':image_area.bottom,'bottom':image_area.bottom-1})
                                cut_orientation = 'horizontal'

                            cut_blocks= split_block(block,cut_line,cut_orientation,
                                                    conf=-1,keep_all=True)
                            if cut_blocks:
                                # final block depends on edge and cut orientation
                                if cut_orientation == 'vertical':
                                    if intersect_edge == 'left':
                                        block = cut_blocks[1] if len(cut_blocks) > 1 else None
                                    elif intersect_edge == 'right':
                                        block = cut_blocks[0]
                                elif cut_orientation == 'horizontal':
                                    if intersect_edge == 'top':
                                        block = cut_blocks[1] if len(cut_blocks) > 1 else None
                                    elif intersect_edge == 'bottom':
                                        block = cut_blocks[0]

                        if block:
                            # add block
                            page.add_child(block.copy())
                    
                # save ocr results
                ocr_results_path = f'{image_path}_ocr_results.json'
                tree.save_json(ocr_results_path)

            # reset ocr editor
            if image_area:
                _,values = window.read(timeout=0)
                # reset image
                values['target_input'] = image_path
                choose_window_image_input(values)

                # reset variables
                refresh_ocr_results()

                # reset ocr results
                if ocr_results_path:
                    values['ocr_results_input'] = ocr_results_path
                    update_canvas_ocr_results(window,values)
                    add_ocr_result_cache(OCR_Tree(ocr_results_path,config['base']['text_confidence']))
                    toggle_ocr_results_block_type(bounding_boxes=get_bounding_boxes(),
                                                  default_color=default_edge_color,
                                                  toogle=values['checkbox_toggle_block_type'])

                # reset sidebar
                sidebar_update_block_info()
                update_sidebar_articles()





def split_ocr_blocks_by_whitespaces_method():
    '''Split ocr blocks by whitespaces. If highlighted blocks, apply only on them. Else, apply on all blocks'''
    global highlighted_blocks,current_ocr_results,image_plot,animation,\
        figure_canvas_agg,config
    bounding_boxes = get_bounding_boxes()
    blocks = highlighted_blocks if highlighted_blocks else bounding_boxes.values()
    last_id = max(current_ocr_results.get_boxes_level(level=2),key=lambda b: b.id).id + 1

    new_blocks = []
    # split by whitespaces on whole results
    split_tree = split_whitespaces(current_ocr_results.copy(),
                                   conf=config['base']['text_confidence'],
                                   debug=config['base']['debug'])
    split_tree_blocks = split_tree.get_boxes_level(level=2)
    split_tree_blocks.sort(key=lambda b: b.id)

    # for each of the relevant blocks, check if they were split
    ## if so, add new block result of split
    for block in blocks:
        block_tree = block['block']
        block_tree:OCR_Tree
        # get same block in split tree
        split_tree_counter_part = split_tree.get_box_id(block_tree.id)
        # check if box stayed the same
        if not block_tree.box == split_tree_counter_part.box:
            print(f'Splitting block {block_tree.id} | box: {split_tree_counter_part.box}')
            # update block
            block_tree.update(split_tree_counter_part)
            create_ocr_block_assets(split_tree_counter_part)
            # add new block
            new_block = split_tree.get_box_id(last_id)
            if new_block:
                print(f'new block: {last_id} | box: {new_block.box}')
                new_block.id = last_id
                last_id += 1
                new_blocks.append(new_block)

    for new_block in new_blocks:
        # add new block to ocr_results
        page = current_ocr_results.get_boxes_level(1)[0]
        page.add_child(new_block)
        # create assets
        create_ocr_block_assets(new_block)

    if highlighted_blocks:
        refresh_highlighted_blocks()
    



def refresh_highlighted_blocks():
    '''Refresh highlighted blocks. Check if they are still valid'''
    global bounding_boxes,highlighted_blocks,block_filter

    print('Refreshing highlighted blocks | Highlighted blocks:',len(highlighted_blocks))
    i = 0
    while i < len(highlighted_blocks):
        b = highlighted_blocks[i]
        if b['id'] not in bounding_boxes:
            highlighted_blocks.remove(b)
            continue

        highlighted_blocks[i] = bounding_boxes[b['id']]
        b = highlighted_blocks[i]
        valid = True
        block = b['block']
        rectangle = b['rectangle']

        # if block filter, check if block is still valid
        if valid and block_filter is not None:
            if not block_filter(block):
                valid = False

        if not valid:
            highlighted_blocks.remove(b)
            rectangle.set_facecolor('none')
            print(f'Removed block {block.id} from highlighted_blocks')
        else:
            rectangle.set_facecolor((1,0,0,0.1))
            i += 1


def refresh_blocks_ids():
    '''Refresh block ids'''
    global bounding_boxes
    unique_ids = set()
    new_bounding_boxes = {}
    for b in bounding_boxes.values():
        id = b['id']
        if id in unique_ids:
            b['id'] += 1
            b['block'].id = b['id']
            b['id_text'].set_text(f'{b["id"]}')
            id = b['id']

        unique_ids.add(id)
        new_bounding_boxes[id] = b

    bounding_boxes = new_bounding_boxes


def change_block_id(id:int,new_id:int):
    '''Change block id'''
    global bounding_boxes
    if id in bounding_boxes:
        b = bounding_boxes[id]
        b['id'] = new_id
        b['block'].id = b['id']
        b['id_text'].set_text(f'{b["id"]}')

        # if new id is already in use, change id of block that use it
        if new_id in bounding_boxes:
            b = bounding_boxes[new_id]
            b['id'] = new_id + 1
            b['block'].id = new_id + 1
            b['id_text'].set_text(f'{new_id+1}')
        refresh_blocks_ids()



def calculate_reading_order_method():
    '''Calculate reading order method'''
    global current_ocr_results,current_image_path,bounding_boxes,config,highlighted_blocks
    if current_ocr_results and current_image_path:

        # if no highlighted blocks, apply calculate reading order
        if not highlighted_blocks:
            # get block order
            ## get body area using delimiters
            delimiters = [b.box for b in current_ocr_results.get_boxes_type(level=2,types=['delimiter'])]
            target_segments = config['methods']['target_segments']
            body_area = segment_document_delimiters(image=current_image_path,delimiters=delimiters,
                                                    target_segments=target_segments)[1]
            ## blocks returned are only part of the body of the image
            ordered_blocks = order_ocr_tree(image_path=current_image_path,ocr_results=current_ocr_results,
                                            area=body_area)
            ordered_block_ids = [b.id for b in ordered_blocks]
            # update ids values
            last_id = len(ordered_blocks) - 1
            for b in bounding_boxes.values():
                if b['id'] not in ordered_block_ids:
                    # block not in order
                    ## update id to be after last_id
                    b['id'] = last_id
                    b['block'].id = b['id']
                    b['id_text'].set_text(f'{b["id"]}')
                    last_id += 1
                else:
                    # block in order
                    ## update id to be position in order list
                    new_id = ordered_block_ids.index(b['id'])
                    b['id'] = new_id
                    b['block'].id = b['id']
                    b['id_text'].set_text(f'{b["id"]}')
        # change ids of highlighted blocks according to order in list
        elif len(highlighted_blocks) > 1:
            last_id = highlighted_blocks[0]['id'] + 1
            for b in highlighted_blocks[1:]:
                # if id is already in use, change id of block that use it
                if last_id in bounding_boxes:
                    same_id_block = bounding_boxes[last_id]
                    same_id_block['id'] = b['id']
                    same_id_block['block'].id = same_id_block['id']
                    same_id_block['id_text'].set_text(f'{same_id_block["id"]}')
                b['id'] = last_id
                b['block'].id = b['id']
                b['id_text'].set_text(f'{b["id"]}')
                last_id += 1
            
        # update ids text
        refresh_blocks_ids()


def fix_ocr_block_intersections_method():
    '''Fix ocr block intersections method. If no highlighted blocks, apply on all blocks. 
    Else, apply on highlighted blocks.'''
    global highlighted_blocks,current_ocr_results,bounding_boxes
    if highlighted_blocks:
        # apply fix
        tree = current_ocr_results.copy()
        tree = block_bound_box_fix(tree,find_delimiters=False,find_images=False,debug=True)
        for highlighted_block in highlighted_blocks:
            block = highlighted_block['block']
            # update highlighted block
            block = tree.get_box_id(id=highlighted_block['id'],level=2)
            current_ocr_results.get_box_id(id=highlighted_block['id']).update(block)
            # update assets
            create_ocr_block_assets(block)

        refresh_highlighted_blocks()
    elif current_ocr_results:
        block_bound_box_fix(current_ocr_results)
        # update assets
        for b in bounding_boxes.values():
            create_ocr_block_assets(b['block'])


def adjust_bounding_boxes_method():
    '''Adjust bounding boxes method. 
    Adjusts bounding boxes according with inside text and text confidence.
    If no highlighted blocks, apply on all blocks. Else, apply on highlighted blocks.'''
    global current_ocr_results,bounding_boxes,highlighted_blocks
    if highlighted_blocks:
        # apply fix
        tree = current_ocr_results.copy()
        tree = text_bound_box_fix(tree,debug=True)
        for highlighted_block in highlighted_blocks:
            block = highlighted_block['block']
            # update highlighted block
            block = tree.get_box_id(id=highlighted_block['id'],level=2)
            current_ocr_results.get_box_id(id=highlighted_block['id']).update(block)
            # update assets
            create_ocr_block_assets(block)

        refresh_highlighted_blocks()
    elif current_ocr_results:
        # apply fix
        text_bound_box_fix(current_ocr_results,debug=True)

        # update assets
        for b in bounding_boxes.values():
            create_ocr_block_assets(b['block'])


def categorize_blocks_method():
    '''Categorize blocks method. If no highlighted blocks, apply on all blocks. 
    Else, apply on highlighted blocks.'''
    global current_ocr_results,bounding_boxes,highlighted_blocks,\
        bounding_boxes,default_edge_color,window,config
    if highlighted_blocks:
        # apply categorize
        tree = current_ocr_results.copy()
        tree = categorize_boxes(tree,conf=config['base']['text_confidence'],
                                override=True,debug=config['base']['debug'])

        for highlighted_block in highlighted_blocks:
            block = highlighted_block['block']
            # update highlighted block
            block = tree.get_box_id(id=highlighted_block['id'],level=2)
            current_ocr_results.get_box_id(id=highlighted_block['id']).update(block)
            # update assets
            create_ocr_block_assets(block)

        refresh_highlighted_blocks()
    elif current_ocr_results:
        # apply categorize
        categorize_boxes(current_ocr_results,conf=config['base']['text_confidence']
                         ,override=True,debug=config['base']['debug'])

        # update assets
        for b in bounding_boxes.values():
            create_ocr_block_assets(b['block'])

    toggle_ocr_results_block_type(bounding_boxes,default_color=default_edge_color,
                                  toogle=window['checkbox_toggle_block_type'].get())


def find_titles_method():
    '''Find titles method.'''
    global current_ocr_results,bounding_boxes,config
    if current_ocr_results:
        og_block_num = len(current_ocr_results.get_boxes_level(2))
        find_text_titles(current_ocr_results,conf=config['base']['text_confidence'],id_blocks=True,
                         categorize_blocks=False,debug=config['base']['debug'])
        new_block_num = len(current_ocr_results.get_boxes_level(2))
        if og_block_num != new_block_num:
            refresh_ocr_results()


def unite_blocks_method():
    '''Unite blocks method.'''
    global current_ocr_results,bounding_boxes
    if current_ocr_results:
        og_block_num = len(current_ocr_results.get_boxes_level(2))
        unite_blocks(current_ocr_results,logs=True)
        new_block_num = len(current_ocr_results.get_boxes_level(2))
        if og_block_num != new_block_num:
            refresh_ocr_results()

def find_articles_method():
    '''Find articles method.'''
    global current_ocr_results,current_image_path,ocr_results_articles
    if current_ocr_results and current_image_path:
        # reset articles
        ocr_results_articles = {}
        _,articles = extract_articles(image_path=current_image_path,
                                      ocr_results=current_ocr_results)
        # choose color for each article
        colors = []
        for _ in articles:
            article_color = unique_article_color(colors)
            colors.append(article_color)

        ocr_results_articles = {i:{'color':colors[i],'article':articles[i]} for i in range(len(articles))}

        draw_articles()
        update_sidebar_articles()


def generate_output_md():
    '''Generate output markdown'''
    global current_ocr_results,current_image_path,ocr_results_articles,config
    if current_ocr_results and current_image_path:
        doc_type = config['methods']['doc_type']
        results_path = config['base']['output_path']
        text_confidence = config['base']['text_confidence']
        ignore_delimiters = config['methods']['ignore_delimiters']
        calculate_reading_order = config['methods']['calculate_reading_order']
        # newspaper
        if doc_type == 'newspaper':
            articles = []
            # get articles
            if not ocr_results_articles:
                _,articles = extract_articles(image_path=current_image_path,
                                              ocr_results=current_ocr_results)
            else:
                only_selected = config['methods']['article_gathering'] == 'selected'

                if only_selected:
                    for id in ocr_results_articles:
                        articles.append(ocr_results_articles[id]['article'])
                else:
                    # get articles using all blocks
                    ## remove all blocks that are already in articles
                    tree = current_ocr_results.copy()
                    for article in ocr_results_articles.values():
                        for block in article['article']:
                            tree.remove_box_id(id=block.id,level=2)
                    ## using unselected blocks
                    _,new_articles = extract_articles(image_path=current_image_path,ocr_results=tree,
                                                      ignore_delimiters=ignore_delimiters,
                                                      calculate_reading_order=calculate_reading_order)
                    ## join all articles
                    articles = [a['article'] for a in ocr_results_articles.values()] + new_articles

            # generate output
            min_text_conf = text_confidence
            with open(f'{results_path}/articles.md','w',encoding='utf-8') as f:
                for article in articles:
                    article = Article(article,min_text_conf)
                    f.write(article.to_md(f'{results_path}'))
                    f.write('\n')
            
            print(f'Output generated: {results_path}/articles.md')
        # simple output
        else:
            calculate_reading_order = config['methods']['calculate_reading_order']
            if calculate_reading_order:
                blocks = order_ocr_tree(current_image_path,current_ocr_results,ignore_delimiters)
            else:
                blocks = [block for block in current_ocr_results.get_boxes_level(2,ignore_type=[] if not ignore_delimiters else ['delimiter'])]
                blocks = sorted(blocks,key=lambda x: x.id)

            with open(f'{results_path}/output.md','w',encoding='utf-8') as f:
                for block in blocks:
                    block_txt = block.to_text(text_confidence)
                    f.write(block_txt)


def add_article_method():
    '''Add article method'''
    global current_ocr_results,ocr_results_articles,highlighted_blocks
    if current_ocr_results and highlighted_blocks:
        # check if highlighted blocks are in articles; if so, remove them from articles
        for block in highlighted_blocks:
            for _,article in ocr_results_articles.items():
                if len([b for b in article['article'] if b.id == block['id']]) > 0:
                    article['article'] = [b for b in article['article'] if b.id != block['id']]

        refresh_articles()

        # create new article with highlighted blocks
        article = []
        for block in highlighted_blocks:
            article.append(block['block'])
        article_color = unique_article_color([a['color'] for a in ocr_results_articles.values()])
        article_id = unique_article_id(list(ocr_results_articles.keys()))
        ocr_results_articles[article_id] = {'color':article_color,'article':article}


def update_article_method(article_id:int):
    '''Update article method'''
    global ocr_results_articles,highlighted_blocks
    if article_id in ocr_results_articles and highlighted_blocks:
        # check if highlighted blocks are in articles; if so, remove them from articles
        for block in highlighted_blocks:
            for id,article in ocr_results_articles.items():
                if id == article_id:
                    continue
                if len([b for b in article['article'] if b.id == block['id']]) > 0:
                    article['article'] = [b for b in article['article'] if b.id != block['id']]


        # update article with highlighted blocks
        article = ocr_results_articles[article_id]['article']
        highlighted_blocks_ids = set([b['id'] for b in highlighted_blocks])
        ## remove blocks that have not been highlighted
        for block in article:
            if block.id not in highlighted_blocks_ids:
                article.remove(block)

        article_blocks_ids = set([b.id for b in article])
        ## add blocks that have been highlighted
        for block in highlighted_blocks:
            if block['id'] not in article_blocks_ids:
                article.append(block['block'])

        ocr_results_articles[article_id]['article'] = article

        refresh_articles()



def delete_article_method(article_id:int):
    '''Delete article method'''
    global ocr_results_articles
    if article_id in ocr_results_articles:
        del ocr_results_articles[article_id]
        refresh_articles()

def move_article_method(article_id:int, up:bool=True):
    '''Move article method'''
    global ocr_results_articles
    if article_id in ocr_results_articles:
        keys = list(ocr_results_articles.keys())
        article_index = keys.index(article_id)
        if up and article_index-1 >= 0:
            # change key order, so that the article is moved one space up
            keys.remove(article_id)
            keys.insert(article_index-1,article_id)
            ocr_results_articles = {k: ocr_results_articles[k] for k in keys}
        elif not up and article_index+1 < len(keys):
            # change key order, so that the article is moved one space down
            keys.remove(article_id)
            keys.insert(article_index+1,article_id)
            ocr_results_articles = {k: ocr_results_articles[k] for k in keys}
        refresh_articles()


def test_method():
    '''Test method'''
    global current_ocr_results,current_image_path,config,window
    print('Test method')
    if current_ocr_results:
        print('Bound box fix image')
        print(current_ocr_results.get_box_id(7).box)
        current_ocr_results = delimiters_fix(current_ocr_results,conf=config['base']['text_confidence'])

        refresh_ocr_results()
        
        add_ocr_result_cache(current_ocr_results)

################################################
###########                   ##################
###########     MAIN LOOP     ##################
###########                   ##################
################################################


def run_gui(input_image_path:str=None,input_ocr_results_path:str=None):
    '''Run GUI'''
    global window,highlighted_blocks,current_ocr_results,current_ocr_results_path,\
            bounding_boxes,ppi,animation,figure,default_edge_color,\
            current_action,block_filter,last_window_size,config,ocr_results_articles

    create_base_folders()
    tmp_folder_path = f'{consts.ocr_editor_path}/tmp'
    # clean tmp folder
    for f in os.listdir(tmp_folder_path):
        if os.path.isfile(os.path.join(tmp_folder_path, f)):
            os.remove(os.path.join(tmp_folder_path, f))
        else:
            shutil.rmtree(os.path.join(tmp_folder_path, f))

    # read config and update dependent variables
    config = read_ocr_editor_configs_file()
    update_config_dependent_variables()

    window = ocr_editor_layout()
    last_window_size = window.size
    event,values = window._ReadNonBlocking()    # for development
    if input_image_path:
        values['target_input'] = input_image_path
    if input_ocr_results_path:
        values['ocr_results_input'] = input_ocr_results_path

    # start values - for development
    if values:
        update_canvas_image(window,values)
        update_canvas_ocr_results(window,values)
        if current_ocr_results:
            add_ocr_result_cache(current_ocr_results)
            update_canvas_column(window)

    # get collapsible sections, and status
    ## elements with key '-collapsible_*-'
    collapsible_sections = [k for k in window.AllKeysDict if f'{k}'.startswith('collapse_')]
    collapsible_sections_status = {}
    for k in collapsible_sections:
        collapsible_sections_status[k] = window[k].visible

    while True:
        event,values = window.read()
        print(event)
        if event == sg.WIN_CLOSED:
            destroy_canvas()
            break
        #---------------------------------
        # MAIN FRAME EVENTS
        #---------------------------------
        # choose image
        elif event == 'target_input':
            choose_window_image_input(values)
        # choose ocr results
        elif event == 'ocr_results_input':
            update_canvas_ocr_results(window,values)
            add_ocr_result_cache(current_ocr_results)
            toggle_ocr_results_block_type(bounding_boxes=bounding_boxes,
                                          default_color=default_edge_color,
                                          toogle=values['checkbox_toggle_block_type'])
        # save ocr results
        elif event == 'save_ocr_results':
            save_ocr_results()
        # save ocr results as copy
        elif event == 'save_ocr_results_copy':
            save_ocr_results(save_as_copy=True)
        # reset ocr results
        elif event == 'reset_ocr_results':
            reset_ocr_results(window)
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # zoom in   
        elif event == 'zoom_in':
            zoom_canvas(factor=-30)
        # zoom out
        elif event == 'zoom_out':
            zoom_canvas(factor=30)
        # generate md
        elif event == 'generate_md':
            generate_output_md()
        # send block back
        elif event == 'send_block_back':
            if len(highlighted_blocks) > 0:
                send_blocks_to_back(highlighted_blocks)
                sidebar_update_block_info()
        # send block forward
        elif event == 'send_block_front':
            if len(highlighted_blocks) > 0:
                send_blocks_to_front(highlighted_blocks)
                sidebar_update_block_info()
        # reset blocks z
        elif event == 'reset_blocks_height':
            reset_blocks_z(bounding_boxes.values())
        # toggle block type
        elif event == 'checkbox_toggle_block_type':
            toggle_ocr_results_block_type(bounding_boxes=bounding_boxes,
                                          default_color=default_edge_color,
                                          toogle=values[event].get())
        # save block changes
        elif event == 'button_save_block':
            save_ocr_block_changes(values=values)
            add_ocr_result_cache(current_ocr_results)
        # delete block
        elif event == 'button_delete_block':
            delete_ocr_block()
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # ocr block
        elif event == 'button_ocr_block':
            apply_ocr_block()
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # copy block text
        elif event == 'button_copy_block_text':
            copy_block_text()
        # toggle articles
        elif event == 'checkbox_toggle_articles':
            toogle = values[event]
            if toogle:
                draw_articles()
            else:
                toggle_ocr_results_block_type(bounding_boxes=bounding_boxes,
                                              default_color=default_edge_color,
                                              toogle=window['checkbox_toggle_block_type'].get())
        # article button
        elif 'table_articles' in event[0]:
            row,_ = event[2]
            if row is not None:
                article_id = int(window['table_articles'].get()[row][0])
                highlight_article(article_id)
        # add article
        elif event == 'button_add_article':
            add_article_method()
            update_sidebar_articles()
            draw_articles()
            reset_highlighted_blocks()
        # update article
        elif event == 'button_update_article':
            selected_row = values['table_articles'][0] if len(values['table_articles']) > 0 else None
            if selected_row is not None:
                article_id = int(window['table_articles'].get()[selected_row][0])
                update_article_method(article_id)
                update_sidebar_articles()
                draw_articles()
                reset_highlighted_blocks()
        # delete article
        elif event == 'button_delete_article':
            # get selected value in article table
            selected_row = values['table_articles'][0] if len(values['table_articles']) > 0 else None
            if selected_row is not None:
                article_id = int(window['table_articles'].get()[selected_row][0])
                delete_article_method(article_id)
                update_sidebar_articles()
                draw_articles()
                reset_highlighted_blocks()
        # move article up
        elif 'button_move_article' in event:
            selected_row = values['table_articles'][0] if len(values['table_articles']) > 0 else None
            if selected_row is not None:
                article_id = int(window['table_articles'].get()[selected_row][0])
                direction_up = True if event.split('_')[-1] == 'up' else False
                move_article_method(article_id,up=direction_up)
                update_sidebar_articles()
                draw_articles()
                reset_highlighted_blocks()
        # create new block
        elif event == 'method_new_block':
            create_new_ocr_block()
            add_ocr_result_cache(current_ocr_results)
        # join blocks
        elif event == 'method_join':
            join_ocr_blocks()
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # split blocks
        elif event == 'method_split':
            # needs to have a single highlighted block
            if len(highlighted_blocks) == 1:
                current_action = 'split_block'
            else:
                sg.popup('Please select a single block to split')
        # filter blocks
        elif 'box_type' in event:
            block_type = event.split('_')[2]
            block_filter = lambda b: b.type == block_type if block_type != 'all' else True
            refresh_highlighted_blocks()
            sidebar_update_block_info()
        # context menu send to back
        elif 'context_menu_send_to_back' in event:
            if len(highlighted_blocks) > 0:
                send_blocks_to_back(highlighted_blocks)
                sidebar_update_block_info()
        # context menu send to front
        elif 'context_menu_send_to_front' in event:
            if len(highlighted_blocks) > 0:
                send_blocks_to_front(highlighted_blocks)
                sidebar_update_block_info()
        # undo last operation
        elif event == 'undo_ocr_results':
            undo_operation()
            sidebar_update_block_info()
            toggle_ocr_results_block_type(bounding_boxes=bounding_boxes,
                                          default_color=default_edge_color,
                                          toogle=values['checkbox_toggle_block_type'])
        # redo last operation
        elif event == 'redo_ocr_results':
            redo_operation()
            sidebar_update_block_info()
            toggle_ocr_results_block_type(bounding_boxes=bounding_boxes,
                                          default_color=default_edge_color,
                                          toogle=values['checkbox_toggle_block_type'])
        # calculate reading order method
        elif event == 'method_calculate_reading_order':
            calculate_reading_order_method()
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # split whitespaces method
        elif event == 'method_split_whitespaces':
            split_ocr_blocks_by_whitespaces_method()
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # remove empty blocks
        elif event == 'method_remove_empty_blocks':
            remove_empty_blocks_method()
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # fix intersections
        elif event == 'method_fix_intersections':
            fix_ocr_block_intersections_method()
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # adjust bounding boxes
        elif event == 'method_adjust_bounding_boxes':
            adjust_bounding_boxes_method()
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # categorize blocks
        elif event == 'method_categorize_blocks':
            categorize_blocks_method()
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # unite blocks
        elif event == 'method_unite_blocks':
            unite_blocks_method()
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # find titles
        elif event == 'method_find_titles':
            find_titles_method()
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # find articles
        elif event == 'method_find_articles':
            find_articles_method()
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # refresh block ids
        elif event == 'method_refresh_block_id':
            refresh_blocks_ids()
            sidebar_update_block_info()
            add_ocr_result_cache(current_ocr_results)
        # split image
        elif event == 'method_split_image':
            if current_action != 'split_image':
                current_action = 'split_image'
            else:
                click_x, click_y = values[event]
                split_image_method(int(click_x),int(click_y))
                current_action = None
                print('split image')
        # test method
        elif event == 'method_test':
            test_method()
        # configurations button
        elif event == 'configurations_button':
            config = run_config_gui(position=window.CurrentLocation())
            update_config_dependent_variables()
        # collapsible section
        elif event.startswith('-OPEN collapse_'):
            # get section key
            section_key = event.split('-OPEN ')[1].split('-')[0]
            # update section status
            section_status = not collapsible_sections_status[section_key]
            collapsible_sections_status[section_key] = section_status
            # update section visibility
            window[section_key].update(visible= section_status)
            # update section arrow
            window[f'-OPEN {section_key}-'].update(SYMBOL_DOWN if section_status else SYMBOL_UP)
            refresh_layout()
            
        else:
            print(f'event {event} not implemented')
        
        # window size changed
        if last_window_size != window.size:
            refresh_layout()
            update_canvas_column(window)

        last_window_size = window.size
    window.close()