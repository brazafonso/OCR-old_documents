import PIL
import cv2
import torch
import layoutparser as lp
import aux_utils.consts as consts
from aux_utils.misc import *
from document_image_utils.image import calculate_dpi
from aux_utils.box import Box
from PIL import Image
from sympy import ceiling



def create_waifu2x_model(method:str='scale2x',model_type:str='photo',noise_level:int=1) -> torch.nn.Module:
    '''Create Waifu2x model'''
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
    if logs:
        print(f'Running Waifu2x | target_image: {target_image} | method: {method} | model_type: {model_type} | noise_level: {noise_level} | result_image_path: {result_image_path}')
        print('Loading model | cuda available: ',torch.cuda.is_available())


    model = None
    PIL.Image.MAX_IMAGE_PIXELS = None # disable PIL.Image.MAX_IMAGE_PIXELS
    input_image = Image.open(target_image)

    # autoscale
    ## discern how many times to run the model
    if method == 'autoscale':
        w,h = input_image.size
        dpi = calculate_dpi(Box(0,w,0,h),Box(0,dimensions[0],0,dimensions[1]))

        if logs:
            print('Auto Scaling image | dpi: ',dpi,' | target_dpi: ',target_dpi)

        if dpi < target_dpi:
            scale_times = ceiling(target_dpi/dpi) - 1
            scaling_type = None
            if scale_times >= 4:
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
            while (scaling_type == 2 and scale_times > 0) or (scaling_type == 4 and scale_times > 1):
                if logs:
                    print('scaling image | scale_times left: ',scale_times,' | scaling_type: ',scaling_type)
                result = model.infer(input_image)
                if not result_image_path:
                    result_image_path = f'{consts.result_path}/{path_to_id(target_image)}/result_waifu2x.png'
                result.save(result_image_path)
                input_image = result

                if scaling_type == 2:
                    scale_times -= 1
                elif scaling_type == 4:
                    scale_times -= 3

            if scale_times > 0:
                model = create_waifu2x_model(method='scale2x',model_type=model_type,noise_level=noise_level)

                result = model.infer(input_image)
                if not result_image_path:
                    result_image_path = f'{consts.result_path}/{path_to_id(target_image)}/result_waifu2x.png'
                result.save(result_image_path)

            if logs:
                w,h = result.size
                dpi = calculate_dpi(Box(0,w,0,h),Box(0,dimensions[0],0,dimensions[1]))
                print('Auto Scaling image | dpi: ',dpi,' | target_dpi: ',target_dpi)



    else:
        model = create_waifu2x_model(method=method,model_type=model_type,noise_level=noise_level)
        if logs:
            print('finished loading model')
            print('running model')


        result = model.infer(input_image)
        if not result_image_path:
            result_image_path = f'{consts.result_path}/{path_to_id(target_image)}/result_waifu2x.png'
        result.save(result_image_path)

    if logs:
        print('finished Waifu2x')

    return result_image_path


# def test_detectron2(image_path:str):
#     from detectron2.utils.logger import setup_logger
#     from detectron2 import model_zoo
#     from detectron2.engine import DefaultPredictor
#     from detectron2.config import get_cfg
#     from detectron2.utils.visualizer import Visualizer
#     from detectron2.data import MetadataCatalog, DatasetCatalog
#     import torchvision

#     TORCH_VERSION = ".".join(torch.__version__.split(".")[:2])
#     CUDA_VERSION = torch.__version__.split("+")[-1]
#     print("torch: ", TORCH_VERSION, "; cuda: ", CUDA_VERSION)
#     print("torchvision: ", torchvision.__version__)
#     print("detectron2:", detectron2.__version__)

#     setup_logger()
#     im = cv2.imread(image_path)
#     cfg = get_cfg()

#     cfg.merge_from_file(model_zoo.get_config_file("lp://PrimaLayout/mask_rcnn_R_50_FPN_3x/config"))
#     cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5  # set threshold for this model
#     cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
#     predictor = DefaultPredictor(cfg)
#     outputs = predictor(im)

#     v = Visualizer(im[:, :, ::-1], MetadataCatalog.get(cfg.DATASETS.TRAIN[0]), scale=1.2)
#     out = v.draw_instance_predictions(outputs["instances"].to("cpu"))
#     out = out.get_image()[:, :, ::-1]
#     out = cv2.resize(out, (1920, 1080))
#     win = cv2.imshow('teste',out)
#     cv2.waitKey(0)


def remove_document_images(image_path:str,logs:bool=False)->cv2.Mat:
    '''Remove document image elements from image, using layout parser.
    Element images:
    - Photograph
    - Illustration
    - Map
    - Comics/Cartoon
    - Editorial Cartoon
    - Advertisement'''

    treated_image = cv2.imread(image_path)
    rgb_image = treated_image[..., ::-1]

    # model = lp.Detectron2LayoutModel(
    #             config_path='lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config', # In model catalog
    #             label_map   ={0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"}, # In model`label_map`
    #             extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.7] # Optional
    #         )

        #     color_map = {
    #     'Text':   'red',
    #     'Title':  'blue',
    #     'List':   'green',
    #     'Table':  'purple',
    #     'Figure': 'pink',
    # }

    model = lp.Detectron2LayoutModel(
                config_path='lp://NewspaperNavigator/faster_rcnn_R_50_FPN_3x/config', # In model catalog
                label_map   ={0: "Photograph", 1: "Illustration", 2: "Map", 3: "Comics/Cartoon", 4: "Editorial Cartoon", 5: "Headline", 6: "Advertisement"}, # In model`label_map`
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.7] # Optional
            )
    
    color_map = {
        'Photograph': 'green',
        'Illustration': 'blue',
        'Map': 'yellow',
        'Comics/Cartoon': 'purple',
        'Editorial Cartoon': 'orange',
        'Headline': 'red',
        'Advertisement': 'gray'
    }


    layout = model.detect(image = rgb_image)

    if logs:
        # analyse blocks
        for block in layout:
            print(f'Block: {block.type} -> {block.score}')
            print('\t\t'+str(block.coordinates))
    
    blocks_to_remove = set(['Photograph', 'Illustration', 'Map', 'Comics/Cartoon', 'Editorial Cartoon'])


    # remove blocks found
    for block in layout:
        if block.type in blocks_to_remove:
            left = int(block.coordinates[0])
            top = int(block.coordinates[1])
            right = int(block.coordinates[2])
            bottom = int(block.coordinates[3])
            if logs:
                print(left, top, right, bottom)

            # remove block
            treated_image = cv2.rectangle(treated_image, (left, top),
                                (right, bottom),
                                (255, 255, 255), -1)
        
    return treated_image