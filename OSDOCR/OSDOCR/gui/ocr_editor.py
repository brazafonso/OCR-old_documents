'''OCR Editor  - GUI'''

import os
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
from OSDOCR.ocr_tree_module.ocr_tree import *

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
## variables for ocr results
bounding_boxes = {}
current_ocr_results = None
current_ocr_results_path = None
## actions
currenct_action = None
last_key = None
last_mouse_position = None
highlighted_block = None
## constants
ppi = 300   # default pixels per inch
max_block_dist = 20 # max distance from a block to a click


def clear_canvas():
    '''Clear canvas'''
    global image_plot,figure_canvas_agg,animation
    print('Clear canvas')
    try:
        if image_plot:
            image_plot = None
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
    global image_plot,figure,figure_canvas_agg,current_image_path,ppi
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
    global image_plot,figure,figure_canvas_agg,ppi,current_image_path,bounding_boxes

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
        bounding_box = Rectangle((left,top),right-left,bottom-top,linewidth=1,edgecolor='g',facecolor='none')
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
            'vertices_circles' : vertices_circles
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


def canvas_on_button_press(event):
    global currenct_action,currenct_action_start,bounding_boxes,highlighted_block
    print(f'click {event}')
    # left click
    if event.button == 1:
        # calculare closest block
        click_x = event.xdata
        click_y = event.ydata
        currenct_action_start = (click_x,click_y)
        block_id = closest_block(click_x,click_y)
        if block_id is not None:
            # print(f'closest block {block_id}')
            block = bounding_boxes[block_id]
            highlighted_block = block
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

        else:
            print('no block found')


def canvas_on_button_release(event):
    global currenct_action
    print(f'release {event}')
    currenct_action = None

def canvas_on_mouse_move(event):
    global currenct_action,last_mouse_position,bounding_boxes,highlighted_block,image_plot
    if currenct_action and highlighted_block and last_mouse_position:
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
            block = highlighted_block['block']
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
                bounding_boxes[highlighted_block['id']]['box'] = box
                # print(f'moved {move_x},{move_y} ! {box}')

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

def run_gui():
    '''Run GUI'''
    global window,current_ocr_results,current_ocr_results_path,bounding_boxes,ppi,animation,figure

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
        else:
            print(f'event {event} not implemented')
    window.close()