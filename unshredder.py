#!/usr/bin/python 

# Copyright (c) 2011 Vasco Fernandes

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from PIL import Image
import sys
import argparse



class ShreddedImage(object):
    def __init__(self, img):
        self.img = img
        self.w,self.h = img.size
        
        self.data = img.getdata()

        self.bw = map(sum, self.data)
        self.columns = [self.bw[i::self.w] for i in range(0, self.w)]

    def diff(self, x, y, cache={}):
        if (x, y) in cache:
            return cache[(x, y)]
        else:
            r = sum(map(lambda x, y: abs(x-y), self.columns[x], self.columns[y]))
            cache[(x, y)] = r
            return r

    def entropy(self, c1, c2, cache={}):
        """Calculate the entropy of a transition between column c1 and c2.
        A a small value indicates the the rhythm of change is maintained 
        throughout the boundary."""

        if c1 == c2: return sys.maxint
        if (c1, c2) in cache:
            return cache[(c1, c2)]
        else:
            e = self.diff(c1, c2)
            
            left = 0
            if c1 > 0: left += self.diff(c1-1, c1)
            if c1 > 1: 
                left += self.diff(c1-2, c1-1)
                left /= 2

            right = 0
            if c2 < self.w-1: right += self.diff(c2, c2+1)
            if c2 < self.w-2:
                right += self.diff(c2+1, c2+2)
                right /= 2

            r = abs((e-left)) + abs((e-right))

            cache[(c1, c2)] = r
            return r

    def set_dividers(self, dividers):
        dividers = [d for d in sorted(dividers) if d > 0 and d < self.w]
        self.blocks = map(lambda x, y: {'start': x, 'end': y-1, 'parts':[(x, y-1)]}, [0] + dividers, dividers + [self.w])

    def guess_dividers(self, even=False):
        #create the difference image from the greyscale data
        diff = map(lambda x, y: abs(x-y), self.bw, self.bw[1:]+[0])

        #the average pixel difference in the image
        avg = sum(diff)/len(diff)

        #divide the difference image in columns
        columns = map(lambda i: diff[i::self.w], range(self.w))
        
        #classify each columns as the number of pixel that changes faster than average
        columns = map(lambda a: reduce(lambda x, y: x+1 if y > avg else x, a, 0), columns)

        #calculate the speed of change from column to column
        diff_columns = map(lambda x, y: y-x, [0] + columns[:-1], columns)

        #a minimal value of change for a column to be considered a divider
        divider_threshold = self.h / 10

        #select the dividers 
        dividers = [i+2 for i, (p, v) in enumerate(zip(diff_columns[:-1], diff_columns[1:])) 
                        if v > divider_threshold]
        
        if even:
            splits = map(lambda x, y: y - x, dividers[:-1], dividers[1:])
            m = max(set(splits), key=splits.count)
            dividers = range(0, self.w, m)

        self.set_dividers(dividers)

    def merge(self):
        """Merge the image blocks using a greedy algorithm according 
        to the entropy of the blocks boundaries."""

        columns = self.columns
        blocks = list(self.blocks)
        nblocks = len(blocks)
        
        entropy_matrix = [self.entropy(b1['end'], b2['start']) for b1 in blocks 
                                                               for b2 in blocks]
        while len(blocks) > 1:
           entropy_matrix = {}

           for i, b1 in enumerate(blocks):
               for j, b2 in enumerate(blocks):
                   if not i == j:
                       entropy_matrix[(i,j)] = self.entropy(b1['end'], b2['start'])

           ((i, j), e) = min(entropy_matrix.items(), key=lambda x: x[1])

           print e
           b1 = blocks[i]
           b2 = blocks[j]

           new_block = {'start':b1['start'], 
                        'end':b2['end'], 
                        'parts': b1['parts']+b2['parts']} 

           if i < j:
               del blocks[j]
               del blocks[i]
           else:
               del blocks[i]
               del blocks[j]

           blocks.append(new_block)
        return blocks[0]

    def unshred(self, even=False, dividers=None):
        #if no predefined blocks are given, guess them
        if not dividers: self.guess_dividers(even)
        else: self.set_dividers(dividers)

        #duplicate image data
        data = list(self.data)
        image_columns = map(lambda i: data[i::self.w], range(self.w))

        #returns the correct ordering of the blocks
        ordered_block = self.merge()

        #arrange the columns according to the correct order
        unshredded_columns = [image_columns[col] for block in ordered_block['parts'] 
                                                 for col in range(block[0], block[1]+1)]

        #create image data from columns
        newdata = tuple(tuple(unshredded_columns[i][j][:3]) for j in range(self.h) 
                                                            for i in range(self.w))
        
        img = Image.new('RGB', (self.w, self.h))
        img.putdata(newdata)
        return img

def unshred(image, even=False, shred=None, bounds=None):
    """Unshred an image according to the bounds.

    Arguments:
    image --- file name of the image to be unshredded.
    even --- Set to True if the boundaries are evenly distributed and size should be guessed.
    shred --- Size of the evenly distributed shreds, if provided it may improve speed.
    bounds --- List containing the columns index at the beginning of each shred.
    output --- The file name where to save the file.

    Returns the unshredded image in PIL format.
    """

    img = Image.open(image)
    shredded_image = ShreddedImage(img)
    if shred: bounds = range(0, img.size[0], shred)

    unshredded_img = shredded_image.unshred(even, bounds)
    
    return unshredded_img


def main():
    parser = argparse.ArgumentParser(description='Unshred an image. You may provide the shredding size, otherwise it will be guessed from the image.',
                                     epilog='You may specify an image with uneven shreds and they will be calculated, however this can be slow for large images.')
    parser.add_argument('image', type=str, help='image file to unshred')
    parser.add_argument('-e', '--even', action='store_true', help='specify that shredding is evenly distributed')
    parser.add_argument('-s', '--shred', type=int, help='specify the size of the evenly distributed shreds')
    parser.add_argument('-b', '--bounds', type=int, nargs='+', help='list of the boundaries of the shreds')
    parser.add_argument('-o', '--output', type=str, help='output file')
    args = parser.parse_args()

    shredding_args = dict(vars(args))
    del shredding_args['output']

    img = unshred(**shredding_args)
    
    output=args.output

    if not output:
        dot = image.rindex('.')
        output = image[:dot] + '.unshredded' + image[dot:]

    img.save(output)

if __name__ == '__main__':
    main()
