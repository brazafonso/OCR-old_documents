import shutil
import PIL
import cv2
import math
import numpy as np
import OSDOCR.aux_utils.consts as consts
from OSDOCR.aux_utils.misc import *
from OSDOCR.aux_utils.box import Box
from document_image_utils.image import calculate_dpi, identify_document_images as identify_document_images_leptonica
from PIL import Image

file_path = os.path.dirname(os.path.realpath(__file__))


def create_waifu2x_model(method:str='scale2x',model_type:str='photo',noise_level:int=1):
    '''Create Waifu2x model'''
    import torch
    if torch.cuda.is_available():
        model = torch.hub.load("nagadomi/nunif:master", "waifu2x",
        method=method, noise_level=noise_level, model_type=model_type,trust_repo=True).to("cuda")
    else:
        model = torch.hub.load("nagadomi/nunif:master", "waifu2x",
        method=method, noise_level=noise_level, model_type=model_type,trust_repo=True).to("cpu")

    return model


def run_waifu2x(target_image:str,method:str='autoscale',model_type:str='photo',noise_level:int=1,result_image_path:str=None,dimensions:tuple[int,int]=(11.7,16.5),target_dpi:int=300,logs:bool=False) -> str:
    '''Run Waifu2x to clean or upscale image.
    
    Args:
        target_image (str): path to image
        method (str, optional): method to use ['scale2x','scale4x',autoscale,'noise']. Defaults to 'scale2x'.
        model_type (str, optional): model type ['photo','art','art_scan']. Defaults to 'photo'.
        noise_level (int, optional): noise level [-1 (None),0,1,2,3]. Defaults to 1.
        result_image_path (str, optional): path to save result. Defaults to None, in which case result will be saved to same directory.
    '''
    import torch
    if logs:
        print(f'Running Waifu2x | target_image: {target_image} | method: {method} | model_type: {model_type} | noise_level: {noise_level} | result_image_path: {result_image_path}')
        print('Loading model | cuda available: ',torch.cuda.is_available())


    model = None
    PIL.Image.MAX_IMAGE_PIXELS = None # disable PIL.Image.MAX_IMAGE_PIXELS
    input_image = Image.open(target_image)


    if not result_image_path:
        result_image_path = f'{consts.result_path}/{path_to_id(target_image)}/result_waifu2x.png'

    # save original image
    input_image.save(result_image_path)

    # autoscale
    ## discern how many times to run the model
    if method == 'autoscale':
        w,h = input_image.size
        dpi = calculate_dpi(Box(0,w,0,h),Box(0,dimensions[0],0,dimensions[1]))

        if logs:
            print('Auto Scaling image | dpi: ',dpi,' | target_dpi: ',target_dpi)

        if dpi < target_dpi:
            scale_times = math.ceil((target_dpi/dpi) / 2)
            scaling_type = None
            if scale_times >= 2:
                model_main = 'scale4x'
                scaling_type = 4
            else:
                model_main = 'scale2x'
                scaling_type = 2

            if logs:
                print('Auto Scaling image | dpi: ',dpi,' | target_dpi: ',target_dpi,' | scale_times: ',scale_times,' | scaling_type: ',scaling_type)

            model = create_waifu2x_model(method=model_main,model_type=model_type,noise_level=noise_level)

            # upscale for scaling times
                # if scaling_type 4, run until scale_times = 1
                    # scale_type 2 is faster for last scale
            while (scaling_type == 2 and scale_times > 0) or (scaling_type == 4 and scale_times > 1) and dpi <= target_dpi:
                w,h = input_image.size
                dpi = calculate_dpi(Box(0,w,0,h),Box(0,dimensions[0],0,dimensions[1]))
                if logs:
                    print('scaling image | current dpi: ',dpi,' | scale_times left: ',scale_times,' | scaling_type: ',scaling_type)
                result = model.infer(input_image)
                result.save(result_image_path)
                input_image = result

                if scaling_type == 2:
                    scale_times -= 1
                elif scaling_type == 4:
                    scale_times -= 3

            if scale_times > 0 and dpi <= target_dpi:
                model = create_waifu2x_model(method='scale2x',model_type=model_type,noise_level=noise_level)

                result = model.infer(input_image)
                result.save(result_image_path)

            if logs:
                w,h = result.size
                dpi = calculate_dpi(Box(0,w,0,h),Box(0,dimensions[0],0,dimensions[1]))
                print('Finished auto scaling image | dpi: ',dpi,' | target_dpi: ',target_dpi)



    else:
        model = create_waifu2x_model(method=method,model_type=model_type,noise_level=noise_level)
        if logs:
            print('finished loading model')
            print('running model')


        result = model.infer(input_image)
        result.save(result_image_path)

    if logs:
        print('finished Waifu2x')

    return result_image_path



def identify_document_images_layoutparser(image_path:str,conf:float=0.5,old_document:bool=True,logs:bool=False)->list[Box]:
    '''Identify document image elements from image, using layout parser.
    Identified image elements (old document):
    - Photograph
    - Illustration
    - Map
    - Comics/Cartoon
    - Editorial Cartoon

    Identified image elements (new document):
    - Table
    - Figure
    
    
    '''

    import layoutparser as lp

    treated_image = cv2.imread(image_path)
    rgb_image = treated_image[..., ::-1]

    model = None
    blocks_to_identify = []
    if old_document:
        model = lp.Detectron2LayoutModel(
                    config_path='lp://NewspaperNavigator/faster_rcnn_R_50_FPN_3x/config', # In model catalog
                    label_map   ={0: "Photograph", 1: "Illustration", 2: "Map", 3: "Comics/Cartoon", 4: "Editorial Cartoon", 5: "Headline", 6: "Advertisement"}, # In model`label_map`
                    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.7] # Optional
        # color_map = {
        #     'Photograph': 'green',
        #     'Illustration': 'blue',
        #     'Map': 'yellow',
        #     'Comics/Cartoon': 'purple',
        #     'Editorial Cartoon': 'orange',
        #     'Headline': 'red',
        #     'Advertisement': 'gray'
        # }
                )
        blocks_to_identify = set(['Photograph', 'Illustration', 'Map', 'Comics/Cartoon', 'Editorial Cartoon'])

    else:

        model = lp.Detectron2LayoutModel(
                    config_path='lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config', # In model catalog
                    label_map   ={0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"}, # In model`label_map`
                    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.7] # Optional
                )
            #     color_map = {
        #     'Text':   'red',
        #     'Title':  'blue',
        #     'List':   'green',
        #     'Table':  'purple',
        #     'Figure': 'pink',
        # }
        blocks_to_identify = set(['Table', 'Figure'])

    


    layout = model.detect(image = rgb_image)

    if logs:
        # analyse blocks
        for block in layout:
            print(f'Block: {block.type} -> {block.score}')
            print('\t\t'+str(block.coordinates))
    
    

    identified_blocks = []
    # remove blocks found
    for block in layout:
        if block.type in blocks_to_identify and block.score > conf:
            left = int(block.coordinates[0])
            top = int(block.coordinates[1])
            right = int(block.coordinates[2])
            bottom = int(block.coordinates[3])
            if logs:
                print(left, top, right, bottom)
            identified_block = Box(left, right, top, bottom)
            identified_blocks.append(identified_block)
        
    return identified_blocks



def remove_image_blocks(image_path:str,blocks:list[Box],logs:bool=False)->cv2.Mat:
    '''Remove blocks from image'''
    image = cv2.imread(image_path)
    average_color = [int(np.average(image[:,:,i])) for i in range(3)]

    for block in blocks:
        # remove block
        ## creates white rectangle over the block
        image = cv2.rectangle(image, (block.left, block.top), (block.right, block.bottom), average_color, -1)

        if logs:
            print(f'Removed block: {block}')

    return image


def identify_document_images(image_path:str,method:str='leptonica',old_document:bool=True,conf:float=0.5,logs:bool=False)->list[Box]:
    '''Identify document images from image'''

    blocks = []
    if method == 'leptonica':
        blocks = identify_document_images_leptonica(image_path,logs=logs)
    else:
        blocks = identify_document_images_layoutparser(image_path,conf=conf,old_document=old_document,logs=logs)

    return blocks


def remove_document_images(image_path:str,method:str='leptonica',conf:float=0.5,old_document:bool=True,save_blocks:bool=False,save_blocks_path:str=None,logs:bool=False)->cv2.Mat:
    '''Remove document images from document. Image blocks will be saved in save_blocks_path folder in file "blocks.json"'''

    blocks = []
    blocks = identify_document_images(image_path,method=method,old_document=old_document,conf=conf,logs=logs)

    # save blocks and their positions
    if save_blocks and save_blocks_path:
        image = cv2.imread(image_path)

        if not os.path.exists(save_blocks_path):
            os.makedirs(save_blocks_path)

        # save blocks
        id = 0
        serialized_blocks = []
        for block in blocks:
            # cut block and save it in folder
            block_img = image[block.top:block.bottom, block.left:block.right]
            cv2.imwrite(f'{save_blocks_path}/{id}.png',block_img)
            serialized_block = block.to_json()
            serialized_block['id'] = id
            serialized_blocks.append(serialized_block)
            id += 1

        # save block positions
        with open(f'{save_blocks_path}/blocks.json','w') as f:
            json.dump(serialized_blocks,f,indent=4)

    return remove_image_blocks(image_path,blocks,logs=logs)


def fix_illumination(image_path:str,model_weight:str='best_SSIM',split_image:bool=True,logs:bool=False)->cv2.typing.MatLike:
    '''Use model from HVI_CIDNet (https://github.com/Fediory/HVI-CIDNet) to fix illumination.

    Split image parameter is used to improve time of processing, althoug for some models it might create different results (as they won't receive the whole picture as input).
    
    Available model weights (https://onedrive.live.com/?authkey=%21ACob5LruXUFfRwY&id=2985DB836826D183%21346&cid=2985DB836826D183):
    - best_SSIM
    - best_PSNR
    - LOL-Blur
    - SICE
    - SID
    - w_perc'''
    from .models.HVI_CIDNet.net.CIDNet import CIDNet
    from .models.HVI_CIDNet.data.data import get_SICE_eval_set
    import torch
    from torchvision import transforms
    from torch.utils.data import DataLoader



    weights_path = f'{consts.osdocr_path}/consts/models/weights/{model_weight}.pth'    
    # check if model exists
    if not os.path.exists(weights_path):
        print(f'Weights not found: {weights_path}. Please download it or check its path.')
        return
    

    # make tmp dir and copy image
    if not os.path.exists(f'{file_path}/tmp'):
        os.makedirs(f'{file_path}/tmp')
    else:
        # clear tmp dir
        for f in os.listdir(f'{file_path}/tmp'):
            os.remove(f'{file_path}/tmp/{f}')

    ## check image shape

    ### if image is grayscale, convert it to RGB
    image = cv2.imread(image_path)
    h, w, c = image.shape
    if c == 1:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

    ### if image is too big (area > 1000*1000), crop into batches
    if h*w > 1000*1000 and split_image:
        n_columns = math.ceil(w/1000)
        n_rows = math.ceil(h/1000)
        batches = []
        for i in range(n_rows):
            batches.append([])
            for j in range(n_columns):
                left = j*1000
                top = i*1000
                right = min(w, (j+1)*1000)
                bottom = min(h, (i+1)*1000)
                batches[i].append(image[top:bottom,left:right])
    else:
        batches = [[image]]

    ## copy image/batches
    for i,row in enumerate(batches):
        for j,column in enumerate(row):
            cv2.imwrite(f'{file_path}/tmp/{i}_{j}.png',column)


    # load model
    model = CIDNet().cuda()
    model.load_state_dict(torch.load(weights_path))
    model.eval()

    # load data/image
    eval_data = DataLoader(dataset=get_SICE_eval_set(f'{file_path}/tmp'), batch_size=1, shuffle=False)

    # run model
    for batch in eval_data:
        with torch.no_grad():
            input, name, h, w = batch[0], batch[1], batch[2], batch[3]
            input = input.to('cuda')
            output = model(input) 
        output = torch.clamp(output, 0, 1)
        output = output[:, :, :h, :w]
        output_img = transforms.ToPILImage()(output.squeeze(0))
        output_img.save(f'{file_path}/tmp/{name[0]}')
    
    # restore image
    tmp_imgs = sorted(os.listdir(f'{file_path}/tmp'))
    files = [[]]
    current_row = 0
    ## create matrix of files according to their coordinates
    for tmp_img in tmp_imgs:
        if tmp_img.endswith('.png'):
            tmp_img_path = f'{file_path}/tmp/{tmp_img}'
            tmp_img_name = tmp_img.split('.')[0]
            row = int(tmp_img_name.split('_')[0])
            if row != current_row:
                files.append([tmp_img_path])
            else:
                files[current_row].append(tmp_img_path)

            current_row = row

    output_img = None
    ## create output image
    for row in files:
        row_img = None
        ## concat columns in row
        for tmp_img in row:
            if row_img is None:
                row_img = cv2.imread(tmp_img)
            else:
                batch_img = cv2.imread(tmp_img)
                row_img = cv2.hconcat([row_img,batch_img])

        # concat row to output
        if output_img is None:
            output_img = row_img
        else:
            output_img = cv2.vconcat([output_img,row_img])

    # remove tmp folder
    shutil.rmtree(f'{file_path}/tmp')

    return output_img
