
'''Old Structured Document OCR - Main program'''
import argparse
import os
import sys

from .ocr_tree_module.ocr_tree_fix import bound_box_fix_image,text_bound_box_fix
from .parse_args import process_args
from .aux_utils.misc import *
from .aux_utils import consts
from .ocr_tree_module.ocr_tree import *
from .preprocessing.image import *
from .pipeline import run_target,run_target_split
from .ocr_tree_module.ocr_tree_analyser import *
from .validation.calibrate import run_calibrate





def run_test():
    '''Run tests'''
    target_image = '/home/braz/projetos/OCR-old_documents/study_cases/simple template/2-1.jpg'
    # target_image = '/home/braz/projetos/OCR-old_documents/study_cases/ideal/AAA-13.png'
    # target_image = '/home/braz/projetos/OCR-old_documents/study_cases/complicated reading order/1-09.jpg'
    # target_image = '/home/braz/projetos/OCR-old_documents/study_cases/rotated/1928_0002.tif'
    print('test','target_image',target_image)
    if target_image:
        # test unite blocks
        ocr_results_path = f'/home/braz/projetos/OCR-old_documents/results/2-1______88a3d1a9c2e7707cb70e8f9afa569005/processed/find_titles.json'
        print('test','ocr_results_path',ocr_results_path)
        ocr_results = OCR_Tree(ocr_results_path)
        # # Frequency tests
        # get_text_sizes(ocr_results,method='savgol_filter',logs=True)
        print(get_text_sizes(ocr_results,method='WhittakerSmoother',logs=True))
        #get_columns(ocr_results,method='savgol_filter',logs=True)
        # get_columns(ocr_results,method='WhittakerSmoother',logs=True)
        # get_columns_pixels(target_image,method='WhittakerSmoother',logs=True)
        #get_journal_areas(ocr_results,logs=True)
        # Waifu2x test
        # result_image_path = f'{consts.result_path}/result_waifu2x.png'
        
        # run_waifu2x(target_image,result_image_path=result_image_path,method='noise',noise_level=3,logs=True)
        # run_waifu2x(target_image,result_image_path=result_image_path,method='noise',noise_level=3,logs=True)
        # run_waifu2x(target_image,result_image_path=result_image_path,method='autoscale',noise_level=-1,logs=True)

        # detectron2 test
        # test_detectron2(target_image)

        # layout parser test
        # images = identify_document_images_layoutparser(target_image,old_document=True,logs=True)
        # images_boxes = []
        # for image in images:
        #     t = OCR_Tree()
        #     t.box = image
        #     images_boxes.append(t)
        # img = draw_bounding_boxes(images_boxes,target_image,draw_levels=[0])
        # cv2.imwrite('test.png',img)
        # images = identify_document_images(target_image)
        # images_boxes = []
        # for image in images:
        #     t = OCR_Tree()
        #     t.box = image
        #     images_boxes.append(t)
        # img = draw_bounding_boxes(images_boxes,target_image,draw_levels=[0])
        # cv2.imwrite('test2.png',img)
        # remove_document_images(target_image,logs=True)

        # test run target split
        # results_path = f'{consts.result_path}/{path_to_id(target_image)}'
        # ocr_results = run_target_split(target_image,f'{results_path}/processed',tesseract_config={'l':'por'},logs=True)
        # img = draw_bounding_boxes(ocr_results,target_image)
        # cv2.imwrite('test.png',img)

        # run fix illumination
        # models = ['best_SSIM','best_PSNR','LOL-Blur','SICE','SID','w_perc']
        # for i in range(len(models)):
        #     model = models[i]
        #     img = fix_illumination(target_image,model_weight=model)
        #     cv2.imwrite(f'test_{model}_patch.png',img)
        #     img = fix_illumination(target_image,model_weight=model,split_image=False)
        #     cv2.imwrite(f'test_{model}_nopatch.png',img)

        # tesseract to hocr
        # from pytesseract import pytesseract
        # target_image = "/home/braz/projetos/OCR-old_documents/results/1-09______a20b0f35bae56a523a0a1e300dec23e4/processed/processed.png"
        # pytesseract.run_tesseract(target_image, 'output',extension='hocr', lang='por', config="hocr")

        # hocr to ocr tree
        # hocr_results = 'test.hocr'
        # from .ocr_tree_module.ocr_tree import OCR_Tree
        # ocr_results = OCR_Tree(hocr_results)
        # ocr_results.save_json('test.json',indent=4)
        # ocr_results.id_boxes()
        # img = draw_bounding_boxes(ocr_results,target_image,id=True)
        # cv2.imwrite('test.png',img)
        # ocr_results.save_hocr('test.hocr')

        # draw journal template
        # metadata = get_target_metadata(target_image)
        # image_info = get_image_info(metadata['target_path'])
        # areas = estimate_journal_template(ocr_results,image_info)
        # print(areas)
        # img = draw_journal_template(areas,metadata['target_path'],line_thickness=6)
        # cv2.imwrite('test.png',img)

        # draw columns
        # target_image = remove_document_images(target_image)
        # target_image = cv2.imread(target_image)
        # target_image = rotate_image(target_image,auto_crop=True)
        # crop = cut_document_margins(target_image)
        # target_image = target_image[crop.top:crop.bottom,crop.left:crop.right]
        # _,body,_ = segment_document(target_image.copy())
        # target_image = target_image[body.top:body.bottom,body.left:body.right]
        # cols = divide_columns(target_image)
        # columns_boxes = []
        # for image in cols:
        #     t = OCR_Tree()
        #     t.box = image
        #     columns_boxes.append(t)

        # img = draw_bounding_boxes(columns_boxes,target_image,draw_levels=[0])
        # cv2.imwrite('test.png',img)


        # test bound_box_fix_image
        # metadata = get_target_metadata(target_image)
        # image = metadata['target_path']
        # print(analyze_text(ocr_results))
        # ocr_results = bound_box_fix_image(ocr_results,image,level=5,debug=False)
        # print(analyze_text(ocr_results)) 

        # x = np.random.randint(0,2,(10,10))
        # x = x == 0
        # print(x)
        # y = np.roll(x,-1,axis=1)
        # y[:,-1] = False
        # print(y)
        # z = np.argwhere(x & y)
        # print(z)

        pass



   




def run_main(args:argparse.Namespace):
    '''Run main program. Allows single image or multiple image list'''

    # create results folder
    if not os.path.exists(consts.result_path):
        os.makedirs(consts.result_path)

    targets = []

    # single target
    if args.target:
        # check if targets exist
        for target in args.target:
            if os.path.exists(target) or os.path.exists(f'{consts.current_path}/{target}'):
                if os.path.exists(target):
                    targets.append(target)
                else:
                    targets.append(f'{consts.current_path}/{target}')
            else:
                print(f'File not found: {target}')
                sys.exit(0)

    # multiple targets
    ## process file
    elif args.file:
        if os.path.exists(args.file[0]) or os.path.exists(f'{consts.current_path}/{args.file[0]}'):
            file = None
            if os.path.exists(args.file[0]):
                file = args.file[0]
            else:
                file = f'{consts.current_path}/{args.file[0]}'

            with open(file) as f:
                for line in f:
                    target = line.strip()
                    if os.path.exists(target):
                        targets.append(target)
                    else:
                        print(f'File not found: {target}')
        else:
            raise FileNotFoundError(f'File not found: {args.file[0]} or {consts.current_path}/{args.file[0]}')
        
    # config target
    elif os.path.exists(consts.config['target_image_path']):
        targets.append(consts.config['target_image_path'])

    else:
        print('No target specified. Please specify a target image or a target file.')
        sys.exit(0)

    # run targets
    if targets:
        for target in targets:
            if args.calibrate:
                calibrate_foder = target
                pipeline_configs_path = args.calibrate[0]
                calibrate_reuse = args.calibrate_no_reuse == False
                run_calibrate(calibration_folder=calibrate_foder,pipeline_configs_path=pipeline_configs_path,
                              reuse_results=calibrate_reuse,logs=args.logs,debug=args.debug)
            else:
                run_target(target,args)


def main():
    print('''
        =============================
        =============================
        ||          OSDOCR         ||
        =============================
        =============================
          ''')
    create_base_folders()
    read_configs()
    args = process_args()

    # create tmp folder
    if not os.path.exists(consts.tmp_path):
        os.makedirs(consts.tmp_path)

    # change result path
    if args.output_folder:
        consts.result_path = args.output_folder


    # test mode
    if args.test:
        run_test()

    # gui mode
    elif args.gui:
        from .gui.osdocr_gui.osdocr_gui import run_gui
        run_gui()

    # normal mode
    else:
        run_main(args)
        

    # clean tmp folder files
    clean_tmp_folder()


if __name__ == '__main__':
    main()
    




