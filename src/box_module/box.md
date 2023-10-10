# Box Element
A box element represents the basic element of an OCR engine result. Inspired by the tesseract boxes, this is an extension of those, so as to create a base for the proprosed transformations and analyses of the project. Different OCR engine results will thus be converted into this type of element.

While with tesseract the result is a dictionary of lists of each parameter, this format uses a list of box elements

## Parameters

- **level** : text level of the box. {1:page, 2:block, 3:paragraph, 4:line, 5:word}

- **page_num** : only meaningful when multiple pages are processed.

- **block_num** : block identifier in which box is inserted

- **line_num** : line identifier in which box is inserted

- **word_num** : word identifier (applicable if level is word)

- **left** : leftmost horizontal value of the box, relative to the left border

- **right** : rightmost horizontal value of the box, relative to the left border

- **top** : topmost vertical value of the box, relative to the upper border

- **bottom** : bottommost vertical value of the box, relative to the upper border

- **width** : width of the box

- **height** : heigth of the box

- **text** : text recognized inside the box

- **conf** : level of confidence in the text

- **type** : type of box. ['delimiter','image','text']
