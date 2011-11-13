from PIL import Image
import sys
import numpy
from pprint import pprint

#def compare_columns(img, c1, c2):
#    w,h = img.size
#    data = img.getdata()
#
#    diff = []
#    for i in range(0, w*h, w):
#        left = data[i+c1]
#        right = data[i+c2]
#        #Color does not hold any information
#        pixel_diff = sum(map(lambda x,y: abs(x-y), left, right))/len(left)
#        print pixel_diff
#        diff.append(pixel_diff)
#    return sum(diff)


#def make_difference_image(img):
#    w,h = img.size
#    data = img.getdata()
#    diff = []

#    diff_image = Image.new('RGB', img.size)

#    for i in range(w*h-1):
#        x = i % w
#        y = i / w
#        left = data[i]
#        right = data[i+1]

#        pixel = [(sum(map(lambda x,y: 255-abs(x-y), left, right))-255)/3]*3
#        diff_image.putpixel((x, y), tuple(pixel[:3]))

    
#    print diff
#    diff_image.save('test.png')

#def most_likely_values(dividers, bw, w):
#    columns = [bw[i::w] for i in range(0, w)]

#    new_dividers = []
#    for right in  dividers:
#        best = right-1, 1000000
#        for left in dividers:
#            left -= 1
#            if left == right: continue
#            entropy = sum(map(lambda x, y: abs(x-y), columns[left], columns[right]))
#            if entropy < best[1]:
#                best = (left, entropy) 
#            #print "%d -> %d: %d" % (left, right, entropy)
#        #return
#        if not right == best[0]+1:
#            new_dividers.append(right)
#            print "%d <- %d: %d" % (right, best[0], best[1])
#    
#    if not len(new_dividers) == len(dividers):
#        return most_likely_values(new_dividers, bw, w)

    
    #for b in blocks:
    #    print "[%d -- %d]" % b

class ShreddedImage(object):
    def __init__(self, img):
        self.img = img
        self.w,self.h = img.size
        
        self.data = img.getdata()

        self.bw = map(sum, self.data)
        self.columns = [self.bw[i::self.w] for i in range(0, self.w)]

    def diff(self, x, y):
        return sum(map(lambda x, y: abs(x-y), self.columns[x], self.columns[y]))

    def entropy(self, c1, c2, cache={}):
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


            r = (e-left) + (e-right)

            cache[(c1, c2)] = r
            return r

    def gess_blocks(self):
        diff = map(lambda x, y: abs(x-y), self.bw, self.bw[1:]+[0])
        avg = sum(diff)/len(diff)

        columns = map(lambda i: diff[i::self.w], range(self.w))
        columns = map(lambda a: reduce(lambda x, y: x+1 if y > avg else x, a, 0), columns)

        diff_columns = map(lambda x, y: abs(x-y), [0] + columns[:-1], columns)

        dividers = []
        for i in range(1, len(diff_columns)):
            p,v = diff_columns[i-1:i+1]
            if v > p and v > 30:
                dividers.append(i+1)

        blocks = map(lambda x, y: {'start': x, 'end': y-1, 'parts':[(x, y-1)]}, [0]+dividers[:-1], dividers)
        self.blocks = blocks

    def merge(self):
        columns = self.columns
        blocks = list(self.blocks)
        
        while len(blocks) > 1:
            entropy_matrix = {}

            for i, b1 in enumerate(blocks):
                for j, b2 in enumerate(blocks):
                    if not i == j:
                        entropy_matrix[(i,j)] = self.entropy(b1['end'], b2['start'])

            ((i, j), e) = min(entropy_matrix.items(), key=lambda x: x[1])
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



#def block_entropy(block, columns):
#    be = sum(entropy(i, i+1, columns) for i in range(block['start'], block['end']))
#    return be / block['end']-block['start']

#def image_entropy(blocks, columns):
#    return sum(map(lambda x, y: entropy(x[1], y[0], columns), blocks[:-1], blocks[1:]))


        
 


#def sort(blocks, bw, w):
#    columns = [bw[i::w] for i in range(0, w)]
#    print "starting sort"

#    for i in range(len(blocks)):
#        first = blocks[i]
#        #first_next = blocks[i]

#       for j in range(len(blocks)-1):
#           second = blocks[j]
#           #second_next = blocks[j+1]

            #status_entropy = (entropy(first[1], first_next[0], columns) +
            #                  entropy(second[1], second_next[0], columns))
            #change_entropy = (entropy(first[1], second_next[0], columns) +
            #                  entropy(second[1], first_next[0], columns))

#            new_blocks = list(blocks)
#            new_blocks[i] = blocks[j]
#            new_blocks[j] = blocks[i]
#             
#            ne = image_entropy(new_blocks, columns)
#            oe = image_entropy(blocks, columns)

            #print "Entropy:", ne, "<", oe

#            if ne < oe:
#                print "Switching", first, "with", second
#                blocks = new_blocks
#                #print "Old entropy", (origin[1], test[0]), old_entropy
#                #print "New entropy", (new[1], test[0]), new_entropy
#                #blocks[i] = second
#                #blocks[j] = first
#                return sort(blocks, bw, w)
#    print blocks




def unshred(img, dividers):
    """Unshred an image according to the dividers.

    Takes and image in PIL format and unshreds it according to the boundaries 
    defined in dividers.

    Arguments:
    img --- image to be unshredded in PIL format.
    dividers --- List containing the columns immediately before a division.

    Returns the unshredded image in PIL format.
    """

    #values = []
    #for i in range(0, img.size[0]-1):
    #    values.append(compare_columns(img, i, i+1))

    #print img.size
    #print "image has", len(values), "columns"
    #for i in range(1,18):
    #    for j in range(-3, 3):
    #        print values[32*i+j],
    #    print
    #make_difference_image(img)


    #print "entropy 637-> 638", entropy(637, 638, columns)
    #print "entropy 638-> 639", entropy(638, 639, columns)
    #print "entropy 639-> 544", entropy(639, 544, columns)
    #print "entropy 544-> 545", entropy(544, 545, columns)
    #print "entropy 545-> 546", entropy(545, 546, columns)

    shredded_image = ShreddedImage(img)
    shredded_image.gess_blocks()

    #blocks = gess_dividers(bw, w, h)
    dividers = range(0, shredded_image.w, 32)
    blocks = map(lambda x, y: {'start': x, 'end': y-1, 'parts':[(x, y-1)]}, dividers, dividers[1:]+[640])
    #for b in blocks:
    #    b['entropy'] = block_entropy(b, columns)
    #pprint(blocks)
    #shredded_image.blocks = blocks

    r = shredded_image.merge()

    data = list(shredded_image.data)
    image_columns = map(lambda i: data[i::shredded_image.w], range(shredded_image.w))

    unshredded_columns = []
    for p in r['parts']:
        init = p[0]
        end = p[1]
        unshredded_columns += image_columns[init:end+1]

    newdata = []
    
    print len(unshredded_columns)
    print len(unshredded_columns[0])

    for j in range(shredded_image.h):
        for i in range(shredded_image.w):
            newdata.append(tuple(unshredded_columns[i][j][:3]))

    result = Image.new('RGB', img.size)
    result.putdata(newdata)
    result.save('test.png')



def main():
    image = Image.open(sys.argv[1])
    unshred(image, [])
    #data = image.getdata()



if __name__ == '__main__':
    main()
