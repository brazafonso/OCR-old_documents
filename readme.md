# **OSDOCR - Old Structured Documents OCR**

This repository provides the project for a thesis of the same name, with the purpose of providing a **Toolkit** for enhancing the manipulation and analysis of OCR results, thus enhancing the final output of OCR.

The study cases for this work were mostly focused on old documents, in particular newspapers for their challenging layouts.

The base of the **Toolkit** is the data structure **OCR Tree**, used to store and represent the results of OCR.

Besides the **Toolkit**, two applications of it are here available: 
* a **Pipeline** for applying OCR; 
* a **OCR Tree Editor** which allows for easy manipulation of **OCR Tree** through a graphical editor;

## **Auxiliary repositories**

* [**document_image_utils**](https://github.com/brazafonso/document_image_processing) : repository that provides some image focused methods for the Toolkit. Also developed in the context of the thesis.
* [**waifu2x**](https://github.com/nagadomi/waifu2x) : module used for image upscaling.
* [**HVI-CIDNet**](https://github.com/Fediory/HVI-CIDNet) : module used for image light correction.


# **OCR Tree**

This structured based on data trees is based on the dictionary based output of Tesseract. It has 5 main node levels:

* page
* block
* paragraph
* line
* word

And the main attributes

* id
* type : specific for the newspaper documents and the methods created surrounding these
* text : only filled on the *word* level
* conf : text confidence


It provides conversion methods to, and from, **HOCR** so as to keep compatibility with defined formats. 

To allow the manipulation of the space dimension of the nodes in the Tree, the auxiliary class **Box* was also developed.

## **Box**

This structure represents the position and dimensions of an entity in a space, assuming that it is of a rectangular shape. It also provides tools for its ease of manipulation, such as moving, scaling, calculating distance, etc.

### **Methods**

#### **Move, Update**

Allow for updating the location of a box. **Move** is a relative update whilst **update** is absolute. **Update** provides an argument to prevent the box from being inverted.

#### **Check if boxes align**

**within_vertical_boxes** and **within_horizontal_boxes** checks if two boxes are aligned through the respective axis, given a specific margin of leeway. A flag can be passed to disable the double way check.

#### **Check if boxes intersect**

**intersects_box** checks if two boxes intersect.

Flags *extend_vertical* and *extend_horizontal* allow for an easier check along each of the axis. *inside* enables a box that is inside another to be considered an intersection.

**intersect_area_box** returns the area of intersection of two boxes. The return value is of type **Box**.

**remove_box_area** can be used to remove a given area (solve intersection) from a box while applying the changes that least affect the original area.

#### **Join boxes**

Using the **join** method, to make it so the dimensions of the original box match the location of the two boxes.

#### **Distances**

**distance_to** provides different methods to calculate the distance between two boxes. These are:

* distance between two specific borders
* closest: tries to discern what is the smallest distance between the boxes by making checks for boxes alignments

**distance_to_point** calculates the distance between the box and a point by verifying the difference between the variation of x and y, relative to box's width and height, to the point.

**closest_edge_point** returns the edge of the box that is closest to a given point. Only returns a string representing the edge.



## **Methods**

### **Convertors**

**OCR Tree**

**JSON**

**HOCR**

**CSV** : only to

**TXT** : only to

### **Id boxes**

**id_boxes** allows for easily giving ids to the whole tree or only specific levels and area. 

Flag *override* makes it so only nodes without id are updated.

*Ids* parameter allows for choosing a specific start point for id count.

### **Get boxes**

**get_box_id**

**get_boxes_level**

**get_boxes_in_area** provides a way for getting boxes that are inside a specific area.

**get_boxes_intersect_area** provides a simpler way for getting boxes that are inside a specific area, or have at least a specific ratio of intersection with it.


### **Text analysis**

**calculate_mean_height** returns the mean height of a level of boxes.

**calculate_character_mean_width** returns the mean width of characters of the text of a node.

**is_text_size** checks if a node's text is of a specified text size, within a given range.

**is_empty** checks if a node has no text

**is_vertical_text** checks if a node with text is vertical text. This is done by analyzing the amount of text (lines and paragraphs) and the box's dimensions. 

Example: if a node has multiple lines and most lines overlap vertically, then it is not vertical text.


### **Check for box alignment**

**boxes_below** and for the other directions, filters a list of given blocks so that it only leaves those that are below and horizontally aligned with the block.

**boxes_directly_below** and for the other directions, works similarly, but filters the list further so it only leaves direct neighbors of a block (no in-between blocks between block and filtered block).


### **Join trees**

**join_trees** is a method for joining two trees into a single one. The children of the second tree will be joined to the first. The order of the trees may be swapped depending on their position, ex.: horizontal join should be between the left tree with the right tree.

Allows for horizontal or vertical join. 

Vertical join is simply uniting the blocks children and their boxes without further verifications.

Horizontal join verifies for joining the children in between current children, or uniting two children according to their position and dimensions, ex.: same level text will be united; same level in the same position will be united alternately according to their coordinates.

If *auto* is given as the orientation for the join, the method will check the positions of the trees and choose automatically.


### **Update bounding box**

Using *update_size*, *update_box*, *update_position* or *scale_dimensions* to update the **Box** of a OCR Tree and recursively the **Box** of it's children.



# **Toolkit**

The Toolkit provides a variety of methods surrounding the **OCR Tree** structure, as well as some related to image and text processing.


# **Pipeline**

# **OCR Tree Editor**


