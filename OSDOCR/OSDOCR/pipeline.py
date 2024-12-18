
import argparse
from pathlib import Path
from OSDOCR.aux_utils.parse_args import *
from OSDOCR.aux_utils.misc import *
from OSDOCR.aux_utils import consts
from OSDOCR.ocr_tree_module.ocr_tree import *
from OSDOCR.ocr_tree_module.ocr_tree_analyser import *
from OSDOCR.ocr_tree_module.ocr_tree_fix import *
from OSDOCR.ocr_engines.engine_utils import *
from OSDOCR.output_module.text import *
from OSDOCR.output_module.journal.article import Article
from OSDOCR.preprocessing.image import *


def save_articles(articles:list[OCR_Tree],o_taget:str,results_path:str,
                  output_types:list[str],min_text_conf:int,fix_hifenization_flag:bool):
    '''Save articles. Type of output is defined in args : markdown, html, txt'''
    metadata = get_target_metadata(o_taget)

    if 'markdown' in output_types:

        with open(f'{results_path}/articles.md','w',encoding='utf-8') as f:
            txt = ''
            for article in articles:
                article = Article(article,min_text_conf)
                txt += article.to_md(f'{results_path}',fix_hifenization_flag) + '\n'

            f.write(txt)

        metadata['output']['markdown'] = f'{results_path}/articles.md'


    if 'txt_simple' in output_types:
        with open(f'{results_path}/articles.txt','w',encoding='utf-8') as f:
            txt = ''
            for article in articles:
                article = Article(article,min_text_conf)
                txt += article.to_txt(fix_hifenization_flag)

            f.write(txt)

        metadata['output']['txt_simple'] = f'{results_path}/articles.txt'

    save_target_metadata(o_taget,metadata)


def output_articles(o_target:str,ocr_results:OCR_Tree,results_path:str,args:argparse.Namespace):
    '''Extract articles from image'''

    metadata = get_target_metadata(o_target)
    target_img_path = metadata['target_path']

    calculate_reading_order = 'calculate_reading_order' not in args.skip_method
    target_segments = args.target_segments
    title_priority = args.title_priority
    if args.logs:
        print(f'''
    Parameters:
        * ignore_delimiters: {args.ignore_delimiters}
        * calculate_reading_order: {calculate_reading_order}
        * target_segments: {args.target_segments}
        * title_priority: {title_priority}''')

    # header,body,footer = segment_document(target_img_path,target_segments=target_segments)
    # areas = [header,body,footer]

    next_block_filter = None
    if title_priority:
        next_block_filter = lambda node: node if node.value.type == 'title' else None


    order_list,articles = extract_articles(image_path=target_img_path,
                                           ocr_results=ocr_results,
                                           ignore_delimiters=args.ignore_delimiters,
                                           calculate_reading_order=calculate_reading_order,
                                           target_segments=args.target_segments,
                                           next_node_filter=next_block_filter,
                                           logs=args.logs,
                                           debug=args.debug)

    if args.debug:
        articles_img = draw_articles(articles,target_img_path)
        cv2.imwrite(f'{results_path}/articles.png',articles_img)

    # draw reading order
    if args.debug:
        # change ids to order
        order_map = {order_list[i]:i for i in range(len(order_list))}
        ocr_results_copy = ocr_results.copy()
        ocr_results_copy.change_ids(order_map)

        image = draw_bounding_boxes(ocr_results_copy,target_img_path,[2],id=True)
        cv2.imwrite(f'{results_path}/reading_order.png',image)


    # save articles
    fix_hifenization_flag = 'fix_hifenization' not in args.skip_method
    save_articles(articles,o_target,results_path,args.output_type,
                  args.text_confidence,fix_hifenization_flag)



def output_default(og_target:str,blocks:list[OCR_Tree],results_path:str,args:argparse.Namespace):
    '''Create default output'''
    metadata = get_target_metadata(og_target)

    fix_hifenization_flag = 'fix_hifenization' not in args.skip_method

    if 'txt' in args.output_type or 'txt_simple' in args.output_type:
        with open(f'{results_path}.txt','w',encoding='utf-8') as f:
            txt = ''
            for block in blocks:
                txt += block.to_text(args.text_confidence)

            if fix_hifenization_flag:
                txt = fix_hifenization(txt)

            f.write(txt)

        metadata['output']['txt'] = f'{results_path}.txt'
        metadata['output']['txt_simple'] = f'{results_path}.txt'
                
            
    if 'markdown' in args.output_type:
        directory_path = Path(results_path).parent
        with open(f'{results_path}.md','w',encoding='utf-8') as f:
            txt = ''
            for block in blocks:
                if block.type == 'image' and block.__getattribute__('image_path'):
                    relative_path = os.path.relpath(block.image_path,directory_path)
                    txt += f'![image]({relative_path})\n'
                else:
                    txt += block.to_text(args.text_confidence)

            if fix_hifenization_flag:
                txt = fix_hifenization(txt)

            f.write(txt)

        metadata['output']['markdown'] = f'{results_path}.md'


    save_target_metadata(og_target,metadata)


def save_output(ocr_results:OCR_Tree,o_target:str,results_path:str,args:argparse.Namespace):
    '''Save default output'''
    if args.logs:
        print('SAVE DEFAULT OUTPUT')

    metadata = get_target_metadata(o_target)
    target_img_path = metadata['target_path']


    calculate_reading_order = 'calculate_reading_order' not in args.skip_method
    output_segments = args.output_segments
    target_segments = args.target_segments

    if args.logs:
        print(f'''
    Parameters:
        * calculate_reading_order: {calculate_reading_order}
        * output_segments: {output_segments}
        * target_segments: {target_segments}''')
    

    header,body,footer = segment_document(target_img_path,target_segments=target_segments)

    areas = [header,body,footer]
    for area in areas:
        print(area)

    if calculate_reading_order:
        title_priority = args.title_priority
        next_block_filter = None
        if title_priority:
            next_block_filter = lambda node: node if node.value.type == 'title' else None
        blocks = order_ocr_tree(image_path=target_img_path,ocr_results=ocr_results,
                                ignore_delimiters=args.ignore_delimiters,
                                area=areas,target_segments=target_segments,
                                next_node_filter=next_block_filter,debug=args.debug)
    else:
        blocks = [block for block in ocr_results.copy().get_boxes_level(2,ignore_type=[] if not args.ignore_delimiters else ['delimiter'])]
        blocks = sorted(blocks,key=lambda x: x.id)

    # divide output according to output segments
    if 'header' in output_segments and header:
        header_area_blocks = ocr_results.get_boxes_intersect_area(areas[0],area_ratio=0.9)
        header_blocks = [block for block in blocks if block in header_area_blocks]
        output_default(o_target,header_blocks,f'{results_path}/header',args)

    if 'body' in output_segments and body:
        body_area_blocks = ocr_results.get_boxes_intersect_area(areas[1],area_ratio=0.9)
        body_blocks = [block for block in blocks if block in body_area_blocks]
        output_default(o_target,body_blocks,f'{results_path}/body',args)

    if 'footer' in output_segments and footer:
        footer_area_blocks = ocr_results.get_boxes_intersect_area(areas[2],area_ratio=0.9)
        footer_blocks = [block for block in blocks if block in footer_area_blocks]
        output_default(o_target,footer_blocks,f'{results_path}/footer',args)

    if 'all' in output_segments:
        output_default(o_target,blocks,f'{results_path}/output',args)





def output_target_results(ocr_results:OCR_Tree,o_target:str,results_path:str,
                          args:argparse.Namespace):
    '''Output target results'''
    if args.logs:
        print('OUTPUT TARGET RESULTS')

    metadata = get_target_metadata(o_target)
    metadata['output'] = {}
    save_target_metadata(o_target,metadata)


    if args.target_type == 'newspaper' and not 'extract_articles' in args.skip_method:
        # extract articles
        if args.logs:
            print('EXTRACT ARTICLES')
        output_articles(o_target,ocr_results,results_path,args)

    save_output(ocr_results,o_target,results_path,args)

    


def image_preprocess(o_target:str,results_path:str,args:argparse.Namespace):
    '''Preprocess image'''
    if args.logs:
        print('IMAGE PREPROCESS')
    processed_image_path = f'{results_path}/processed.png'

    metadata = get_target_metadata(o_target)
    metadata['target_path'] = processed_image_path
    metadata['transformations'] = [] if 'transformations' not in metadata else metadata['transformations']
    

    # save image
    og_img = cv2.imread(o_target)
    cv2.imwrite(processed_image_path,og_img)

            
    # image rotation
    if args.fix_rotation and 'auto_rotate' not in args.skip_method:
        if args.logs:
            print('FIX ROTATION')

        rotate_img = rotate_image(processed_image_path,direction=args.fix_rotation,
                                  auto_crop=True,debug=args.debug)
        cv2.imwrite(processed_image_path,rotate_img)

        # create step img
        step_img_path = f'{results_path}/fix_rotation.png'
        cv2.imwrite(step_img_path,rotate_img)

        metadata['transformations'].append(('fix_rotation',args.fix_rotation))



    # remove document margins
    if 'remove_document_margins' not in args.skip_method:
        if args.logs:
            print('REMOVE DOCUMENT MARGINS')

        # remove document margins
        cut_margins = cut_document_margins(processed_image_path)
        
        image = cv2.imread(processed_image_path)
        treated_image = image[cut_margins.top:cut_margins.bottom,
                              cut_margins.left:cut_margins.right]
        cv2.imwrite(processed_image_path,treated_image)

        # create step img
        step_img_path = f'{results_path}/remove_document_margins.png'
        cv2.imwrite(step_img_path,treated_image)

        metadata['transformations'].append(('remove_document_margins'))


    # image upscaling
    if 'image_upscaling' not in args.skip_method:
        if args.logs:
            print('IMAGE UPSCALING')

        if args.upscaling_image:
            method = args.upscaling_image[0]
            upscaled = False

            if method == 'waifu2x':
                tmp_upsacled_image_path = f'{consts.tmp_path}/OSDOcr_image_upscaled_tmp.png'
                method_config = None
                if len(args.upscaling_image) > 1:
                    method_config = args.upscaling_image[1]

                target_dpi = args.target_dpi
                page_dimensions = get_dimensions(args.target_dimensions if args.target_dimensions else 'A3')
                page_dimensions = (page_dimensions['width'],page_dimensions['height'])

                if method_config:
                    run_waifu2x(processed_image_path,
                                result_image_path=tmp_upsacled_image_path,
                                method=method_config,target_dpi=target_dpi,
                                dimensions=page_dimensions,logs=args.debug) 
                else:
                    run_waifu2x(processed_image_path,
                                result_image_path=tmp_upsacled_image_path,
                                target_dpi=target_dpi,dimensions=page_dimensions,
                                logs=args.debug)

                upscaled_img = cv2.imread(tmp_upsacled_image_path)
                cv2.imwrite(processed_image_path,upscaled_img)
                upscaled = True

                # update tesseract config dpi
                w,h = upscaled_img.shape[1],upscaled_img.shape[0]

                dpi = calculate_dpi(Box(0,w,0,h),Box(0,page_dimensions[0],0,page_dimensions[1]))
                args.tesseract_config['dpi'] = round(dpi)

            if upscaled:
                # create step img
                step_img_path = f'{results_path}/image_upscaling.png'
                cv2.imwrite(step_img_path,upscaled_img)

                metadata['transformations'].append(('image_upscaling',method,method_config))

    # remove document images
    if 'remove_document_images' not in args.skip_method:
        if args.logs:
            print('REMOVE DOCUMENT IMAGES')

        method = args.remove_document_images[0]
        old_document = args.target_old_document
        # remove document images
            # also save them so they can be restored later
        images_folder = f'{results_path}/document_images'
        treated_image = remove_document_images(processed_image_path,method=method,
                                               logs=args.debug,old_document=old_document,
                                               save_blocks=True,save_blocks_path=images_folder)
        cv2.imwrite(processed_image_path,treated_image)

        # create step img
        step_img_path = f'{results_path}/remove_document_images.png'
        cv2.imwrite(step_img_path,treated_image)

        metadata['transformations'].append(('remove_document_images',images_folder))


    # noise removal
    if 'noise_removal' not in args.skip_method:
        if args.logs:
            print('NOISE REMOVAL')

        if args.denoise_image:
            method = args.denoise_image[0]
            tmp_denoised_image_path = f'{consts.tmp_path}/OSDOcr_image_denoised_tmp.png'
            denoised = False

            if method == 'waifu2x':
                method_config = None
                if len(args.denoise_image) > 1:
                    method_config = int(args.denoise_image[1])

                if method_config:
                    run_waifu2x(processed_image_path,method='noise',
                                noise_level=method_config,
                                result_image_path=tmp_denoised_image_path,logs=args.debug) 
                else:
                    run_waifu2x(processed_image_path,method='noise',
                                result_image_path=tmp_denoised_image_path,logs=args.debug)

                denoised_img = cv2.imread(tmp_denoised_image_path)
                cv2.imwrite(processed_image_path,denoised_img)
                denoised = True

            if denoised:
                # create step img
                step_img_path = f'{results_path}/noise_removal.png'
                cv2.imwrite(step_img_path,denoised_img)

                metadata['transformations'].append(('noise_removal',method,method_config))


    # lightning correction
    if 'light_correction' not in args.skip_method:
        if args.logs:
            print('LIGHTNING CORRECTION')

        if args.light_correction:
            model_weight = args.light_correction[0]
            split_image = args.light_correction_split_image
            light_corrected = False

            try:
                light_corrected_img = fix_illumination(processed_image_path,model_weight=model_weight,
                                                   split_image=split_image,logs=args.debug)
            except Exception as e:
                print(e)
                light_corrected_img = None

            if light_corrected_img is not None:
                cv2.imwrite(processed_image_path,light_corrected_img)
                light_corrected = True

            if light_corrected:
                # create step img
                step_img_path = f'{results_path}/light_correction.png'
                cv2.imwrite(step_img_path,light_corrected_img)

                metadata['transformations'].append(('light_correction',method,method_config))


    # update metadata
    save_target_metadata(o_target,metadata)

    return processed_image_path


def binarize_image(o_target:Union[str,cv2.typing.MatLike],args:argparse.Namespace):
    '''Binarize image'''
    binarized = None
    if isinstance(o_target,str):
        binarized = cv2.imread(o_target)
    else:
        binarized = o_target.copy()

    if 'binarize_image' not in args.skip_method:
        method = args.binarize_image[0]
        if method == 'fax':
            binarized = binarize_fax(binarized)
        elif method == 'otsu':
            denoise_strength = float(args.binarize_image[1]) if len(args.binarize_image) > 1 else None
            binarized = binarize(binarized,denoise_strength=denoise_strength)

    return binarized





def run_target_split(o_target:str,results_path:str,args:argparse.Namespace)->OCR_Tree:
    '''Segment target into Header, Body, Footer and run OCR on each part. 
    Body is further split into columns.
    
    Final OCR results are then merged into single ocr_tree.'''

    metadata = get_target_metadata(o_target)
    target_path = metadata['target_path']

    target_image = cv2.imread(target_path)
    padding_vertical = int(0.01 * target_image.shape[0])
    padding_horizontal = int(0.01 * target_image.shape[1])

    target_segments = args.target_segments
    target_header = 'header' in target_segments
    target_footer = 'footer' in target_segments


    # segment target
    ## get header, body and footer (only body is guaranteed to be found)
    ## split body into columns
    header,body,footer = segment_document(target_image)

    if args.logs:
        print(f'Body: {body}')
        print(f'Header: {header}')
        print(f'Footer: {footer}')

    header = header if header.valid() and target_header else None
    footer = footer if footer.valid() and target_footer else None

    # if not header, body top is top of image 
    if not header:
        body.top = 0

    # if not footer, body bottom is bottom of image
    if not footer:
        body.bottom = target_image.shape[0]

    image_body = target_image[body.top:body.bottom,body.left:body.right]
    image_header = target_image[header.top:header.bottom,header.left:header.right] if header else None
    image_footer = target_image[footer.top:footer.bottom,footer.left:footer.right] if footer else None


    columns = divide_columns(image_body)
    columns_images = [image_body[column.top:column.bottom,column.left:column.right] for column in columns]

    if args.logs:
        print(f'Columns: {[c.__str__() for c in columns]}')

    # save images into tmp files
    ## create tmp folder
    tmp_folder = f'{results_path}/tmp_segmentation'
    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)

    ## save images
    if header:
        # add padding (for better OCR, in case text is too close to edge)
        avg_color = np.average(image_header,axis=(0,1))
        image_header = cv2.copyMakeBorder(image_header,padding_vertical,
                                          padding_vertical,padding_horizontal,
                                          padding_horizontal,cv2.BORDER_CONSTANT,
                                          value=avg_color)
        b_image_header = binarize_image(image_header,args)
        cv2.imwrite(f'{tmp_folder}/header.png',b_image_header)
    if footer:
        # add padding
        avg_color = np.average(image_footer,axis=(0,1))
        image_footer = cv2.copyMakeBorder(image_footer,padding_vertical,
                                          padding_vertical,padding_horizontal,
                                          padding_horizontal,cv2.BORDER_CONSTANT,
                                          value=avg_color)
        b_image_footer = binarize_image(image_footer,args)
        cv2.imwrite(f'{tmp_folder}/footer.png',b_image_footer)
    for i in range(len(columns_images)):
        # add padding
        avg_color = np.average(columns_images[i],axis=(0,1))
        columns_images[i] = cv2.copyMakeBorder(columns_images[i],padding_vertical,
                                               padding_vertical,padding_horizontal,
                                               padding_horizontal,cv2.BORDER_CONSTANT,
                                               value=avg_color)
        b_columns_image = binarize_image(columns_images[i],args)
        cv2.imwrite(f'{tmp_folder}/column_{i}.png',b_columns_image)

    # OCR
    header_ocr = None
    footer_ocr = None
    columns_ocr = []
    ## header
    if header:
        run_tesseract(f'{tmp_folder}/header.png',results_path=results_path,
                      opts=args.tesseract_config,logs=args.debug)
        header_ocr = OCR_Tree(f'{results_path}/ocr_results.json')

    ## footer
    if footer:
        run_tesseract(f'{tmp_folder}/footer.png',results_path=results_path,
                      opts=args.tesseract_config,logs=args.debug)
        footer_ocr = OCR_Tree(f'{results_path}/ocr_results.json')

    ## columns
    for i in range(len(columns_images)):
        run_tesseract(f'{tmp_folder}/column_{i}.png',results_path=results_path,
                      opts=args.tesseract_config,logs=args.debug)
        column_ocr = OCR_Tree(f'{results_path}/ocr_results.json')
        columns_ocr.append(column_ocr)


    # Merge ocr_trees

    ## update position of header to match real position in target
    if header:
        # remove padding
        header_ocr.update_position(top=-padding_vertical,left=-padding_horizontal,
                                   absolute=False)

    ## update position of columns to match real position in target
    add_top = header.bottom if header else 0 # value to add to all top positions
    add_top -= padding_vertical # remove padding
    for i in range(len(columns_ocr)):
        column = columns_ocr[i]
        column:OCR_Tree
        # value to add according to columns to left of this column
        add_left = columns[i].left - padding_horizontal


        if args.logs:
            print(f'update position of column {i} to {add_left} + {add_top}')

        column.update_position(left=add_left,top=add_top,absolute=False)
        columns[i] = column

    ## update position of footer to match real position in target
    if footer:
        footer_ocr.update_position(top=body.bottom - padding_vertical,
                                   left=-padding_horizontal,absolute=False)

    ## merge all ocr_trees
    results_ocr = OCR_Tree()
    

    if header:
        results_ocr.join_trees(header_ocr)

    for column in columns_ocr:
        results_ocr.join_trees(column)

    if footer:
        results_ocr.join_trees(footer_ocr)


    # save png
    img = draw_bounding_boxes(results_ocr,target_image)
    cv2.imwrite(f'{results_path}/ocr_results.png',img)

    return results_ocr



    




def run_target_image(o_target:str,results_path:str,args:argparse.Namespace):
    '''Run pipeline for single image.
    - Image preprocessing
    - OCR
    - Convert to ocr_tree

    Return ocr_tree and image path (in case of preprocessing)
    '''
    target = o_target

    # preprocess image
    target = image_preprocess(o_target,results_path,args)

            
    if args.logs:
        print(f'OCR: {target}')

    
    # OCR
    ## Segment target and OCR each segment
    if args.segmented_ocr:
        ocr_results = run_target_split(o_target,results_path,args)
        # save ocr results
        with open(f'{results_path}/ocr_results.json','w',encoding='utf-8') as f:
            json.dump(ocr_results.to_json(),f,indent=4)

    ## Simple OCR
    else:
        # binarize
        binarize_tmp  = binarize_image(target,args)
        cv2.imwrite(f'{results_path}/binarize.png',binarize_tmp )
        binarized_path  = f'{results_path}/binarize.png'

        run_tesseract(binarized_path ,results_path=results_path,
                      opts=args.tesseract_config,logs=args.debug)

    # update metadata
    metadata = get_target_metadata(o_target)
    metadata['ocr'] = True
    metadata['ocr_results_path'] = f'{results_path}/ocr_results.json'
    

    # create image blocks in OCR results
    if metadata_has_transformation(metadata,'remove_document_images'):
        _,blocks_path = metadata_get_transformation(metadata,'remove_document_images')

        if os.path.exists(blocks_path):
            blocks_positions_file_path = f'{blocks_path}/blocks.json'
            blocks = json.load(open(blocks_positions_file_path,'r'))

            ocr_results = OCR_Tree(metadata['ocr_results_path'])
            page = ocr_results.get_boxes_level(1)[0]
            for block in blocks:
                ocr_block = OCR_Tree({'level':2,'box':block,'type':'image'})
                ocr_block.image_id = block['id']
                ocr_block.image_path = f'{blocks_path}/{block["id"]}.png'
                page.add_child(ocr_block)

            # save ocr results
            result_dict_file = open(f'{results_path}/ocr_results_image_blocks.json','w')
            json.dump(ocr_results.to_json(),result_dict_file,indent=4)
            result_dict_file.close()
            metadata['ocr_results_path'] = f'{results_path}/ocr_results_image_blocks.json'


    # identify image delimiters
    if 'identify_document_delimiters' not in args.skip_method:
        delimiters = get_document_delimiters(target,debug=False)
        metadata['transformations'].append(('identify_document_delimiters'))
        ocr_results = OCR_Tree(metadata['ocr_results_path'])

        ocr_results.id_boxes(level=[2])

        # add delimiters to ocr results
        page = ocr_results.get_boxes_level(1)[0]
        for delimiter in delimiters:
            ocr_block = OCR_Tree({'level':2,'box':delimiter,'type':'delimiter'})
            page.add_child(ocr_block)

        # save ocr results
        result_dict_file = open(f'{results_path}/ocr_results_delimiters.json','w')
        json.dump(ocr_results.to_json(),result_dict_file,indent=4)
        result_dict_file.close()
        metadata['ocr_results_path'] = f'{results_path}/ocr_results_delimiters.json'

        # save image
        img = draw_bounding_boxes(ocr_results,target)
        cv2.imwrite(f'{results_path}/identify_document_delimiters.png',img)


    metadata['ocr_results_original_path'] = metadata['ocr_results_path']
    save_target_metadata(o_target,metadata)

    # get results
    return [OCR_Tree(metadata['ocr_results_path']),target]


def clean_ocr(ocr_results:OCR_Tree,o_target:str,results_path:str,args:argparse.Namespace):
    '''Clean ocr_tree'''

    if args.logs:
        print('------------------------------------------')
        print('------------------------------------------')
        print('CLEAN OCR')
        print('------------------------------------------')

    metadata = get_target_metadata(o_target)
    target_img = metadata['target_path']

    find_images_flag = metadata_get_transformation(metadata,'remove_document_images') is None
    find_delimiters_flag = metadata_get_transformation(metadata,'identify_document_delimiters') is None
    bound_box_fix_image_flag = 'bound_box_fix_image' not in args.skip_method
    split_whitespaces_flag = 'split_whitespaces' not in args.skip_method


    # remove text of low confidence
    if args.logs:
        print('------------------------------------------')
        print('\tRemove text of low confidence')
        print('------------------------------------------')
    ocr_results.remove_nodes_conf(conf=args.text_confidence)

    # remove empty boxes
    if args.logs:
        print('------------------------------------------')
        print('\tRemoving empty boxes')
        print(f'''\t\tParameters:
\t\t\t* text_confidence: {args.text_confidence}
\t\t\t* find_images: {find_images_flag}
\t\t\t* find_delimiters: {find_delimiters_flag}''')
        print('------------------------------------------')
    ocr_results = remove_empty_boxes(ocr_results,text_confidence=args.text_confidence,
                                      find_images=find_images_flag,find_delimiters=find_delimiters_flag,
                                      debug=args.debug)
    
    if bound_box_fix_image_flag:
        # adjust bounding boxes of text by analyzing image
        if args.logs:
            print('------------------------------------------')
            print('\tAdjust bounding boxes of text by analyzing image')
            print('------------------------------------------')
        ocr_results = bound_box_fix_image(ocr_results,target_img,level=5,
                                        text_confidence=args.text_confidence,debug=args.debug)


    # clean bounding boxes according to text confidence
    if args.logs:
        print('------------------------------------------')
        print('\tClean bounding boxes according to text confidence')
        print('------------------------------------------')
    ocr_results = bound_box_fix(ocr_results,5,None,
                                text_confidence=args.text_confidence ,debug=args.debug)

    if split_whitespaces_flag:
        if args.logs:
            print('------------------------------------------')
            print('\tSpliting blocks by whitespaces')
            print('------------------------------------------')
        ocr_results = split_whitespaces(ocr_results,conf=args.text_confidence,
                                        dif_ratio=args.split_whitespace,debug=args.debug)

    # clean delimiters
    if args.logs:
        print('------------------------------------------')
        print('\tCleaning delimiters')
        print('------------------------------------------')

    if args.debug:
        delimiters = ocr_results.get_boxes_type(level=2,types=['delimiter'])
        print('delimiters:',len(delimiters))
        img = draw_bounding_boxes(delimiters,target_img)
        cv2.imwrite(f'{results_path}/delimiters_1.png',img)

    ocr_results = delimiters_fix(ocr_results,conf=args.text_confidence,debug=args.debug)

    if args.debug:
        delimiters = ocr_results.get_boxes_type(level=2,types=['delimiter'])
        print('delimiters:',len(delimiters))
        img = draw_bounding_boxes(delimiters,target_img)
        cv2.imwrite(f'{results_path}/delimiters_2.png',img)

    # clean bounding boxes of blocks
    if args.logs:
        print('------------------------------------------')
        print('\tBlock bounding box cleaning')
        print('------------------------------------------')
    ocr_results = bound_box_fix(ocr_results,2,None,text_confidence=args.text_confidence,
                                find_images=find_images_flag,find_delimiters=find_delimiters_flag ,
                                debug=args.debug)


    # save ocr results
    result_dict_file = open(f'{results_path}/clean_ocr.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()


    # draw boxes (for debug)
    image = draw_bounding_boxes(ocr_results,target_img,[2],id=True)
    cv2.imwrite(f'{results_path}/clean_ocr.png',image)
    csv = pd.DataFrame(ocr_results.to_dict())
    csv.to_csv(f'{results_path}/ocr_results_processed.csv')

    # save metadata
    metadata['ocr_results_path'] = f'{results_path}/clean_ocr.json'
    metadata['transformations'].append('clean_ocr')
    save_target_metadata(o_target,metadata)

    return ocr_results


def unite_ocr_blocks(ocr_results:OCR_Tree,o_target:str,results_path:str,args:argparse.Namespace):
    '''Unite ocr_tree'''
    

    ocr_results = unite_blocks(ocr_results,conf=args.text_confidence,debug=args.debug)

    # small extra cleaning
    ocr_results = remove_solo_words(ocr_results,conf=args.text_confidence,debug=args.debug)
    ocr_results = delimiters_fix(ocr_results,conf=args.text_confidence,debug=args.debug)



    result_dict_file = open(f'{results_path}/result_united.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    metadata = get_target_metadata(o_target)
    target_img = metadata['target_path']

    image = draw_bounding_boxes(ocr_results,target_img,[2],id=True)
    cv2.imwrite(f'{results_path}/result_united.png',image)
    csv = pd.DataFrame(ocr_results.to_dict())
    csv.to_csv(f'{results_path}/result_united.csv')

    # save metadata
    metadata['ocr_results_path'] = f'{results_path}/result_united.json'
    metadata['transformations'].append('unite_ocr_blocks')
    save_target_metadata(o_target,metadata)

    return ocr_results


def restore_document_images(o_target:str,results_path:str,logs:bool=False):
    '''Restore document images'''

    if logs:
        print('Restoring document images...')

    metadata = get_target_metadata(o_target)
    metadata['transformations'].append('restore_document_images')

    if metadata_has_transformation(metadata,'remove_document_images'):
        _,blocks_path = metadata_get_transformation(metadata,'remove_document_images')

        if os.path.exists(blocks_path):
            blocks_positions_file_path = f'{blocks_path}/blocks.json'
            blocks = json.load(open(blocks_positions_file_path,'r'))

            target_image = metadata['target_path']
            image = cv2.imread(target_image)

            for block in blocks:
                left = block['left']
                top = block['top']
                right = block['right']
                bottom = block['bottom']
                block_id = block['id']
                block_image_path = f'{blocks_path}/{block_id}.png'

                if os.path.exists(block_image_path):
                    block_image = cv2.imread(block_image_path)
                    image[top:bottom,left:right] = block_image

            # create step image
            cv2.imwrite(f'{results_path}/restore_document_images.png',image)

            metadata['target_path'] = f'{results_path}/restore_document_images.png'

    save_target_metadata(o_target,metadata)


def identify_images_ocr_results(ocr_results:OCR_Tree,o_target:str,results_path:str,
                                args:argparse.Namespace):
    '''Identify images in ocr_results'''
    if args.logs:
        print('IDENTIFY DOCUMENT IMAGES')

    metadata = get_target_metadata(o_target)

    target_path = metadata['target_path']
    
    images = identify_document_images_layoutparser(target_path,old_document=args.target_old_document,
                                                   logs=args.debug)
    
    #id ocr results
    ocr_results.id_boxes(level=[2])
    last_id = len(ocr_results.get_boxes_level(level=2))
    ocr_page = ocr_results.get_boxes_level(level=1)[0]
    images_ids = []

    for image in images:
        ocr_block = OCR_Tree({'level':2,'box':image,'type':'image','id':last_id})
        ocr_page.add_child(ocr_block)
        images_ids.append(last_id)
        last_id += 1

    # for each image, delete ocr blocks inside it
    for image_id in images_ids:
        ocr_results.remove_blocks_inside(image_id,args.debug)

    # save ocr results
    result_dict_file = open(f'{results_path}/identify_document_images.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()

    image = draw_bounding_boxes(ocr_results,target_path,[2],id=True)
    cv2.imwrite(f'{results_path}/identify_document_images.png',image)

    # save metadata
    metadata['ocr_results_path'] = f'{results_path}/identify_document_images.json'
    metadata['transformations'].append('identify_images_ocr_results')
    save_target_metadata(o_target,metadata)

    return ocr_results


def find_title_blocks(ocr_results:OCR_Tree,o_target:str,results_path:str,args:argparse.Namespace):
    '''From ocr_results, searches within text blocks for titles and separatest them from the rest'''


    # small cleaning
    ocr_results = find_text_titles(ocr_results,conf=args.text_confidence,
                                   id_blocks=False,categorize_blocks=False,debug=args.debug)

    result_dict_file = open(f'{results_path}/find_titles.json','w')
    json.dump(ocr_results.to_json(),result_dict_file,indent=4)
    result_dict_file.close()


    # save metadata
    metadata = get_target_metadata(o_target)
    target_img = metadata['target_path']
    metadata['ocr_results_path'] = f'{results_path}/find_titles.json'
    metadata['transformations'].append('find_title_blocks')
    save_target_metadata(o_target,metadata)


    image = draw_bounding_boxes(ocr_results,target_img,[2],id=True)
    cv2.imwrite(f'{results_path}/find_titles.png',image)


    return ocr_results







def run_target(target:str,args:argparse.Namespace):
    '''Run pipeline for single target.
    
    - A : image
    1. Analyze target 
    2. Preprocess image
    3. OCR
    4. Convert to ocr_tree


    - B : hOCR/json
    1. Convert to ocr_tree

    - General
    1. Clean ocr_tree
    2. Analyse ocr_tree
    3. Extract articles
    4. Save articles

    '''
    create_target_results_folder(target)

    results_path = f'{consts.result_path}/{path_to_id(target)}'
    processed_path = f'{results_path}/processed'
    original_target_path = target
    metadata = get_target_metadata(target)

    if args.logs:
        print(f'Processing: {target}')
        print(f'Options: {args}')

    apply_ocr = True
    ocr_results_path = args.target_ocr_results[0] if args.target_ocr_results else None
    ocr_results_path:str
    # check if target is hOCR
    if ocr_results_path and ocr_results_path.endswith(('.hocr','.json')) and os.path.exists(ocr_results_path):
        apply_ocr = False

    ocr_results = None

    # use existing ocr results
    if not apply_ocr:
        if args.debug:
            print('Using existing ocr results. |',ocr_results_path)
        ocr_results = OCR_Tree(ocr_results_path)
    # apply ocr
    else:
        force_ocr = args.force_ocr
        # check if target has been ocrd before or force
        if force_ocr or not metadata['ocr']:
            metadata_clean_transformations(metadata)
            ocr_results,_ = run_target_image(original_target_path,processed_path,args)
            
            # get most recent metadata
            metadata = get_target_metadata(original_target_path)

        else:
            if os.path.exists(metadata['ocr_results_original_path']):
                if args.logs:
                    print('Using existing ocr results. |',metadata['ocr_results_original_path'])
                ocr_results_path = metadata['ocr_results_original_path']
                ocr_results = OCR_Tree(ocr_results_path,args.text_confidence)
            else:
                print('File not found: ',ocr_results_path)
                print('Please run ocr first')
                sys.exit(1)

    target = metadata['target_path']

    # id boxes
    ocr_results.id_boxes([2],override=False)

    if args.debug:
        id_img = draw_bounding_boxes(ocr_results,target,[2],id=True)
        cv2.imwrite(f'{processed_path}/result_id_0.png',id_img)

    # clean ocr_results
    if 'clean_ocr' not in args.skip_method:
        if args.logs:
            print('CLEAN OCR')
        ocr_results = clean_ocr(ocr_results,original_target_path,processed_path,args) 

    if args.debug:
        id_img = draw_bounding_boxes(ocr_results,target,[2],id=True)
        cv2.imwrite(f'{processed_path}/result_id_1.png',id_img)

    # categorize boxes
    ocr_results = categorize_boxes(ocr_results,conf=args.text_confidence,debug=args.debug)

    if args.debug:
        id_img = draw_bounding_boxes(ocr_results,target,[2],id=True)
        cv2.imwrite(f'{processed_path}/result_id_2.png',id_img)

    # unite same type blocks
    if 'unite_blocks' not in args.skip_method:
        if args.logs:
            print('UNITE BLOCKS')
        ocr_results = unite_ocr_blocks(ocr_results,original_target_path,processed_path,args)

    if args.debug:
        id_img = draw_bounding_boxes(ocr_results,target,[2],id=True)
        cv2.imwrite(f'{processed_path}/result_id_3.png',id_img)

    if 'find_titles' not in args.skip_method:
        if args.logs:
            print('FIND TITLES')
        ocr_results = find_title_blocks(ocr_results,original_target_path,processed_path,args)

    if args.debug:
        id_img = draw_bounding_boxes(ocr_results,target,[2],id=True)
        cv2.imwrite(f'{processed_path}/result_id_4.png',id_img)

    if args.debug:
        # analyse ocr_results
        results = analyze_text(ocr_results)
        print(results)

    restore_document_images(original_target_path,processed_path,args.debug)

    # output
    if 'output' not in args.skip_method:
        output_target_results(ocr_results,original_target_path,results_path,args)

