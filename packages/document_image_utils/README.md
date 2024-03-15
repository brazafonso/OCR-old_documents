# Contextualization

In progress toolkit for document image pre processing.

Aimed for images to be OCRed.

# Available methods

- Auto rotate image

    Uses left margin of a document to calculate the angle of rotation present, and correct it accordingly.

    Can be given the rotation direction (clocwise or counter_clockwise), or in auto mode tries to determine the side to which the document is tilted (can be none, in which case image won't be rotated).

- Calculate rotation direction

    Calculates rotation direction of an image by finding the biggest sets of the first black pixels appearances (with outliers removed) in the image for each direction: clockwise, counter_clockwise and none.

    For none direction, the set is created based on pixels with same 'x' coordinate that with less than a 5% height difference, relative to the image's height.