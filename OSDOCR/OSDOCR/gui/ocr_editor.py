'''OCR Editor  - GUI'''

import os
import shutil
import traceback
import cv2
import matplotlib
import matplotlib.patches
import matplotlib.pyplot as plt
import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle, Rectangle
from matplotlib.animation import FuncAnimation
from OSDOCR.aux_utils import consts
from OSDOCR.aux_utils.misc import *
import matplotlib.text
import matplotlib.typing
import numpy as np
from .layouts.hocr_editor import *
from .aux_utils.utils import *
from OSDOCR.ocr_tree_module.ocr_tree import *
from OSDOCR.ocr_engines.engine_utils import run_tesseract

# allow matplotlib to use tkinter
matplotlib.use('TkAgg')

# global variables
window = None
## variables for canvas
image_plot = None
current_image_path = None
figure_canvas_agg = None
figure = None
animation = None
default_edge_color = None
## variables for ocr results
bounding_boxes = {}
current_ocr_results = None
current_ocr_results_path = None
## actions
currenct_action = None
currenct_action_start = None
last_key = None
last_mouse_position = None
highlighted_blocks = []
## constants
ppi = 300   # default pixels per inch
max_block_dist = 20 # max distance from a block to a click


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

def refresh_canvas():
    '''Redraws canvas with current ocr results'''
    global window,current_image_path,current_ocr_results,image_plot
    if current_image_path or current_ocr_results:
        if current_image_path:
            # draw image
            clear_canvas()
            # create new plot
            image_plot = create_plot(current_image_path)
            # update canvas
            update_canvas(window,figure)

        if current_ocr_results:
            # draw ocr results
            draw_ocr_results(current_ocr_results,window)

        # warn column of content change
        update_canvas_column(window)


def update_canvas_column(window:sg.Window):
    '''Update canvas column'''
    print('Update canvas column')
    window.refresh()
    window['canvas_body'].contents_changed()

def update_canvas(window:sg.Window,figure):
    '''Update canvas'''
    global figure_canvas_agg,animation,bounding_boxes
    if figure:
        if bounding_boxes:
            animation = FuncAnimation(figure, update, frames=60, blit=True,interval=1000/60,repeat=True)
        # update canvas
        canvas = window['canvas']
        ## use TKinter canvas
        tkcanvas = canvas.TKCanvas
        figure_canvas_agg = FigureCanvasTkAgg(figure, tkcanvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    


def update(frame):
    '''Update canvas'''
    global bounding_boxes
    assets = []
    if bounding_boxes:
        # update position of boxes and id texts
        for block in bounding_boxes.values():
            box = block['box']
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

    return assets

def create_plot(path:str):
    '''Create plot with image'''
    global ppi,figure
    # read image
    image = cv2.imread(path)
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

    return ax




def update_canvas_image(window:sg.Window,values:dict):
    '''Update canvas image element. Creates new plot with image'''
    global image_plot,figure,figure_canvas_agg,current_image_path,ppi,default_edge_color
    if values['target_input']:
        path = values['target_input']
        results_path = f'{consts.result_path}/{path_to_id(path)}'
        metadata = get_target_metadata(path)

        if not metadata:
            # message to OCR image first
            sg.popup('Please OCR image first')
            return

        target_img_path = metadata['target_path']

        if not os.path.exists(target_img_path):
            # message to OCR image first
            sg.popup('Please rerun OCR on target image first')
            return
        
        current_image_path = target_img_path

        # update default edge color for ocr results
        default_edge_color = get_average_inverse_color(target_img_path)
        color = default_edge_color * 255
        color = (int(color[0]),int(color[1]),int(color[2]))
        window['text_default_color'].update(text_color = rgb_to_hex(color))

        clear_canvas()
        # create new plot
        image_plot = create_plot(target_img_path)
        # update canvas
        update_canvas(window,figure)

        # update browse location for 'ocr_results_input'
        window['browse_file'].InitialFolder = f'{results_path}/processed'
        # update browse location for 'target_input'
        window['browse_image'].InitialFolder = os.path.dirname(path)

def update_canvas_ocr_results(window:sg.Window,values:dict):
    '''Update canvas ocr_results element. Creates new plot with ocr_results'''
    global current_ocr_results,current_ocr_results_path
    if values['ocr_results_input']:
        current_ocr_results_path = values['ocr_results_input']

        if not os.path.exists(current_ocr_results_path):
            # message to OCR image first
            sg.popup('Please rerun OCR on target image first')
            return
        
        # read ocr results
        current_ocr_results = OCR_Tree(current_ocr_results_path)
        ## draw ocr results in canvas
        draw_ocr_results(current_ocr_results,window)


def draw_ocr_results(ocr_results:OCR_Tree,window:sg.Window):
    '''Draw ocr results in canvas'''
    global image_plot,figure,figure_canvas_agg,ppi,current_image_path,bounding_boxes,default_edge_color

    # get new plot to draw ocr results
    image_plot = create_plot(current_image_path)

    # id blocks and get them
    ocr_results.id_boxes(level=[2])
    blocks = ocr_results.get_boxes_level(level=2)

    bounding_boxes = {}
    # draw ocr results
    for block in blocks:
        # bounding box
        box = block.box
        left = box.left
        top = box.top
        right = box.right
        bottom = box.bottom
        # draw bounding box (rectangle)
        bounding_box = Rectangle((left,top),right-left,bottom-top,linewidth=1,edgecolor=default_edge_color,facecolor='none')
        image_plot.add_patch(bounding_box)
        vertices = box.vertices()
        vertices_circles = []
        # draw vertices
        for vertex in vertices:
            x,y = vertex
            vertex_circle = Circle((x,y),radius=4,edgecolor='b',facecolor='b')
            image_plot.add_patch(vertex_circle)
            vertices_circles.append(vertex_circle)
        # draw id text in top left corner of bounding box
        id_text = matplotlib.text.Text(left+15,top+30,block.id,color='r',fontproperties=matplotlib.font_manager.FontProperties(size=10))
        image_plot.add_artist(id_text)

        # save bounding box in dictionary
        bounding_boxes[block.id] = {
            'rectangle':bounding_box,
            'block':block,
            'box':box,
            'id_text' : id_text,
            'id' : block.id,
            'vertices_circles' : vertices_circles,
            'click_count' : 0
        }
        

    # clear canvas
    clear_canvas()
    # update canvas
    update_canvas(window,figure)


def closest_block(click_x,click_y):
    '''Get closest block to click. Returns block id'''
    global bounding_boxes,max_block_dist
    block_id = None
    if bounding_boxes:
        # calculate distances
        calculate_distances = np.vectorize(lambda x: {
            'distance':x['box'].distance_to_point(click_x,click_y),
            'id':x['id']
            })
        distances = calculate_distances(list(bounding_boxes.values()))
        # get closest
        closest_block = min(distances,key=lambda x: x['distance'])
        closest_block_id = closest_block['id']
        closest_block_dist = closest_block['distance']
        # print(f'closest block {closest_block_id} distance {closest_block_dist}')
        # check if distance is less than max_block_dist
        if closest_block_dist <= max_block_dist:
            block_id = closest_block_id
    return block_id


def sidebar_update_block_info():
    global window,highlighted_blocks

    if highlighted_blocks:
        block = highlighted_blocks[-1]['block']
        block:OCR_Tree
        # update block info
        ## id
        window['text_block_id'].update(block.id)
        ## coordinates
        left = int(block.box.left)
        top = int(block.box.top)
        right = int(block.box.right)
        bottom = int(block.box.bottom)
        window['text_block_coords'].update(f'({left},{top}) - ({right},{bottom})')
        ## type
        if block.type:
            window['list_block_type'].update(block.type)
        ## text
        text_delimiters = {3: '#Par#'}
        window['input_block_text'].update(block.to_text(conf=0,text_delimiters=text_delimiters))
    else:
        # clear block info
        window['text_block_id'].update('')
        window['text_block_coords'].update('')
        window['list_block_type'].update('')
        window['input_block_text'].update('')



def create_new_ocr_block(x:int=None,y:int=None):
    '''Create new ocr block. If x and y are not None, create new block at that point. Else create new block at middle of canvas'''
    global bounding_boxes,current_ocr_results,figure,default_edge_color,image_plot

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
    box = new_block.box
    left = box.left
    top = box.top
    right = box.right
    bottom = box.bottom
    new_rect = Rectangle((x,y),width=50,height=50,edgecolor=default_edge_color,facecolor='none',linewidth=1)
    image_plot.add_patch(new_rect)
    vertices_circles = []
    vertices = box.vertices()
    for vertex in vertices:
            x,y = vertex
            vertex_circle = Circle((x,y),radius=4,edgecolor='b',facecolor='b')
            image_plot.add_patch(vertex_circle)
            vertices_circles.append(vertex_circle)
    # draw id text in top left corner of bounding box
    id_text = matplotlib.text.Text(left+15,top+30,new_block.id,color='r',fontproperties=matplotlib.font_manager.FontProperties(size=10))
    image_plot.add_artist(id_text)
    bounding_boxes[new_id] = {
        'rectangle':new_rect,
        'block':new_block,
        'box':new_block.box,
        'id_text' : id_text,
        'id' : new_id,
        'vertices_circles' : vertices_circles,
        'click_count' : 0
    }




def canvas_on_button_press(event):
    global currenct_action,currenct_action_start,bounding_boxes,highlighted_blocks
    print(f'click {event}')
    # left click
    if event.button == 1:
        # calculate closest block
        click_x = event.xdata
        click_y = event.ydata
        currenct_action_start = (click_x,click_y)
        block_id = closest_block(click_x,click_y)
        if block_id is not None:
            # print(f'closest block {block_id}')
            block = bounding_boxes[block_id]
            ## check if block is already highlighted
            if block in highlighted_blocks:
                ## change to last index
                highlighted_blocks.remove(block)
                block['click_count'] += 1
            else:
                block['click_count'] = 1

            highlighted_blocks.append(block)
            # update rectangle to have transparent red facecolor
            rectangle = block['rectangle']
            rectangle.set_facecolor((1,0,0,0.1))
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
                    currenct_action = 'move'
                    # print(f'move action ! {block_box}')
                    # move
                else:
                    currenct_action = 'expand'
            
            ### expand
            else:
                currenct_action = 'expand'

            # update block info in sidebar

        else:
            if highlighted_blocks:
                for block in highlighted_blocks:
                    # clear facecolor
                    rectangle = block['rectangle']
                    rectangle.set_facecolor((1,1,1,0))
                    # reset click count
                    block['click_count'] = 0
                    
            highlighted_blocks = []
            print('no block found')


        sidebar_update_block_info()
    # middle click
    elif event.button == 2:
        ## create new block
        click_x = event.xdata
        click_y = event.ydata
        create_new_ocr_block(x=click_x,y=click_y)





def canvas_on_button_release(event):
    global currenct_action,currenct_action_start
    print(f'release {event}')
    release_x = event.xdata
    release_y = event.ydata
    # if click on a block and highlighted_blocks and click without moving, diselect block
    if highlighted_blocks and (currenct_action_start[0] == release_x and currenct_action_start[1] == release_y):
        block_id = closest_block(release_x,release_y)
        if block_id is not None:
            block = bounding_boxes[block_id]
            block_box = block['block'].box
            block_box:Box
            if block_box.distance_to_point(release_x,release_y) == 0 and block['click_count'] > 1:
                highlighted_blocks.remove(block)
                block['rectangle'].set_facecolor((1,1,1,0))

    currenct_action = None

def canvas_on_mouse_move(event):
    global currenct_action,last_mouse_position,bounding_boxes,highlighted_blocks,image_plot
    if currenct_action and highlighted_blocks and last_mouse_position:
        if currenct_action == 'move':
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
                    # print(f'moving {move_x},{move_y} ! {block.box}')
                    block.update_position(top=move_y,left=move_x)
                    bounding_boxes[highlighted_block['id']]['box'] = block.box
                    # print(f'moved {move_x},{move_y} ! {block.box}')

        elif currenct_action == 'expand':
            # calculate new dimensions
            ## start position
            last_x = last_mouse_position[0]
            last_y = last_mouse_position[1]
            ## mouse position
            new_x = event.xdata
            new_y = event.ydata
            ## check which vertex is being moved (closest vertex)
            block = highlighted_blocks[-1]['block']
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
                bounding_boxes[highlighted_blocks[-1]['id']]['box'] = box
                # print(f'moved {move_x},{move_y} ! {box}')

        sidebar_update_block_info()

    last_mouse_position = (event.xdata,event.ydata)


def canvas_on_key_press(event):
    global last_key,ppi
    print(f'key {event.key}')
    if event.key == 'ctrl++':
        ppi -= 30
        print(f'ppi {ppi}')
        refresh_canvas()
    elif event.key == 'ctrl+-':
        ppi += 30
        print(f'ppi {ppi}')
        # reset canvas
        refresh_canvas()


    last_key = event.key


def canvas_on_key_release(event):
    global last_key
    last_key = None


def destroy_canvas():
    global image_plot,figure_canvas_agg
    if image_plot is not None:
        image_plot.remove()
        image_plot = None
    if figure_canvas_agg is not None:
        figure_canvas_agg.get_tk_widget().forget()
        figure_canvas_agg = None


def save_ocr_results(path:str=None,save_as_copy:bool=False):
    '''Save ocr results'''
    global current_ocr_results,current_ocr_results_path
    if current_ocr_results:
        save_path = path if path else current_ocr_results_path
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


def reset_ocr_results(window:sg.Window):
    '''Reset ocr results'''
    global current_ocr_results
    if current_ocr_results and current_ocr_results_path:
        current_ocr_results = OCR_Tree(current_ocr_results_path)
        # draw ocr results in canvas
        draw_ocr_results(current_ocr_results,window)


def toggle_ocr_results_block_type(bounding_boxes:dict,default_color:str='#283b5b',toogle:bool=False):
    '''Change color of bounding boxes based on block type'''

    for b in bounding_boxes.values():
        rectangle = b['rectangle']
        block = b['block']
        block:OCR_Tree
        block_color = default_color
        if toogle and block.type:
            block_color = block.type_color(normalize=True,rgb=True)
        
        rectangle.set_edgecolor(block_color)


def save_ocr_block_changes(values:dict):
    '''Save changes to current highlighted block. 
    The coordinates will be divided equally within the block.
    Confidence of words will be set to 100.'''
    global current_ocr_results,highlighted_blocks

    if current_ocr_results and highlighted_blocks:
        block = highlighted_blocks[-1]['block']
        block:OCR_Tree
        rectangle = highlighted_blocks[-1]['rectangle']
        # get new info from frame 'frame_block_info'
        ## block type ('list_block_type')
        block_type = values['list_block_type']
        ## block text ('input_block_text')
        block_text = values['input_block_text']
        ### turn block text into OCR Tree
        #### count number of paragraphs in line, to be able to divide coordinates equally
        lines = [l for l in block_text.split('\n') if l.strip()]
        pars = [[]]
        for i,line in enumerate(lines):
            if re.match(r'^\s*#Par#\s*$',line,re.IGNORECASE):
                ## ignore if current paragraph is empty
                if len(pars[-1]) > 0:
                    pars.append([])
            else:
                pars[-1].append(line)

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
                line_tree = OCR_Tree({'level':4,'box':{'left':line_left,'top':line_top,'right':line_right,'bottom':line_bottom},'par_num':i,'line_num':j})
                line_words = [w for w in line.split(' ') if w.strip()]

                ##### word level
                for m,word in enumerate(line_words):
                    word_width = int(par_right - par_left) // len(line_words)
                    word_top = line_top
                    word_left = line_left + word_width * m
                    word_right = word_left + word_width
                    word_bottom = line_bottom
                    word_tree = OCR_Tree({'level':5,'box':{'left':word_left,'top':word_top,'right':word_right,'bottom':word_bottom},'text':word,'conf':100,'par_num':i,'line_num':j,'word_num':m})
                    line_tree.add_child(word_tree)

                par_children.append(line_tree)

            if par_children:
                par_tree = OCR_Tree({'level':3,'box':{'left':par_left,'top':par_top,'right':par_right,'bottom':par_bottom},'children':par_children})
                new_children.append(par_tree)

        block.children = new_children
        # change block type
        if block_type and block_type != block.type:
            block.type = block_type
            ## change color of rectangle if type color is toogled
            if values['checkbox_toggle_block_type']:
                color = block.type_color(normalize=True,rgb=True)
                print(color)
                rectangle.set_edgecolor(color)


def delete_ocr_block():
    '''Delete highlighted ocr block'''
    global highlighted_blocks,current_ocr_results,bounding_boxes
    if highlighted_blocks:
        block = highlighted_blocks[-1]
        ## remove block from ocr_results
        current_ocr_results.remove_box_id(block['block'].id)
        ## remove block from bounding_boxes
        del bounding_boxes[block['block'].id]
        ## remove block from highlighted_blocks
        highlighted_blocks.remove(block)


def apply_ocr_block():
    '''Apply OCR on highlighted ocr block'''
    global highlighted_blocks,current_image_path
    if highlighted_blocks:
        block = highlighted_blocks[-1]
        ocr_block = block['block']
        ocr_block:OCR_Tree
        box = ocr_block.box
        # cut part of image
        image = cv2.imread(current_image_path)
        left = int(box.left)
        top = int(box.top)
        right = int(box.right)
        bottom = int(box.bottom)
        image = image[top:bottom,left:right]
        # add some padding
        padding = 20
        avg_color = np.average(image,axis=(0,1))
        image = cv2.copyMakeBorder(image,padding,padding,padding,padding,cv2.BORDER_CONSTANT,value=avg_color)
        # save tmp image
        dir_path = os.path.dirname(current_image_path)
        tmp_dir = f'{dir_path}/tmp'
        os.makedirs(tmp_dir,exist_ok=True)
        tmp_path = f'{tmp_dir}/tmp.png'
        cv2.imwrite(tmp_path,image)
        # run ocr
        run_tesseract(tmp_path,results_path=tmp_dir,opts={'l':'por'})
        # load ocr results
        ocr_results = OCR_Tree(f'{tmp_dir}/ocr_results.json')
        ## move ocr results to position of ocr block
        ocr_results.update_position(top=box.top,left=box.left)
        new_children = ocr_results.get_boxes_level(3)
        ocr_block.children = new_children
        # # remove tmp dir
        # shutil.rmtree(tmp_dir)
        


def join_ocr_blocks():
    '''Join highlighted ocr blocks'''
    global highlighted_blocks,bounding_boxes,current_ocr_results

    if not highlighted_blocks:
        return
    
    blocks = highlighted_blocks.copy()
    # sort blocks by highest
    blocks.sort(key=lambda b:b['block'].box.top)
    while len(blocks) > 1:
        first = blocks[0]['block']
        second = blocks[1]['block']
        first.join_trees(second)
        # remove second block
        ## remove second block from ocr_results
        current_ocr_results.remove_box_id(second.id)
        ## remove second block from bounding_boxes
        del bounding_boxes[second.id]
        ## remove second block from highlighted_blocks
        highlighted_blocks.remove(blocks[1])
        ## remove second block from blocks
        blocks.remove(blocks[1])


def run_gui():
    '''Run GUI'''
    global window,highlighted_blocks,current_ocr_results,current_ocr_results_path,bounding_boxes,ppi,animation,figure,default_edge_color

    window = ocr_editor_layour()
    event,values = window._ReadNonBlocking()
    if values:
        update_canvas_image(window,values)
        update_canvas_ocr_results(window,values)

    while True:
        event,values = window.read()
        print(event)
        if event == sg.WIN_CLOSED:
            destroy_canvas()
            break
        elif event == 'target_input':
            if current_image_path:
                # reset variables
                figure = None
                current_ocr_results = None
                current_ocr_results_path = None
                bounding_boxes = None
                ppi = 300
        
            update_canvas_image(window,values)
            print('Chose target image')
        elif event == 'ocr_results_input':
            update_canvas_ocr_results(window,values)
        elif event == 'save_ocr_results':
            save_ocr_results()
        elif event == 'save_ocr_results_copy':
            save_ocr_results(save_as_copy=True)
        elif event == 'reset_ocr_results':
            reset_ocr_results(window)
        elif event == 'checkbox_toggle_block_type':
            toggle_ocr_results_block_type(bounding_boxes=bounding_boxes,default_color=default_edge_color,toogle=values[event])
        elif event == 'button_save_block':
            save_ocr_block_changes(values=values)
        elif event == 'button_delete_block':
            delete_ocr_block()
            sidebar_update_block_info()
        elif event == 'button_ocr_block':
            apply_ocr_block()
            sidebar_update_block_info()
        elif event == 'method_join':
            join_ocr_blocks()
            sidebar_update_block_info()
        elif event == 'method_new_block':
            create_new_ocr_block()
        else:
            print(f'event {event} not implemented')
    window.close()