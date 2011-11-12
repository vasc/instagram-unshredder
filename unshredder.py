from PIL import Image
import sys
import numpy
from pprint import pprint

def compare_columns(img, c1, c2):
    w,h = img.size
    data = img.getdata()

    diff = []
    for i in range(0, w*h, w):
        left = data[i+c1]
        right = data[i+c2]
        #Color does not hold any information
        pixel_diff = sum(map(lambda x,y: abs(x-y), left, right))/len(left)
        print pixel_diff
        diff.append(pixel_diff)
    return sum(diff)


def make_difference_image(img):
    w,h = img.size
    data = img.getdata()
    diff = []

    diff_image = Image.new('RGB', img.size)

    for i in range(w*h-1):
        x = i % w
        y = i / w
        left = data[i]
        right = data[i+1]

        pixel = [(sum(map(lambda x,y: 255-abs(x-y), left, right))-255)/3]*3
        diff_image.putpixel((x, y), tuple(pixel[:3]))

    
    print diff
    diff_image.save('test.png')

def most_likely_values(dividers, bw, w):
    columns = [bw[i::w] for i in range(0, w)]

    new_dividers = []
    for right in  dividers:
        best = right-1, 1000000
        for left in dividers:
            left -= 1
            if left == right: continue
            entropy = sum(map(lambda x, y: abs(x-y), columns[left], columns[right]))
            if entropy < best[1]:
                best = (left, entropy) 
            #print "%d -> %d: %d" % (left, right, entropy)
        #return
        if not right == best[0]+1:
            new_dividers.append(right)
            print "%d <- %d: %d" % (right, best[0], best[1])
    
    if not len(new_dividers) == len(dividers):
        return most_likely_values(new_dividers, bw, w)

    
    #for b in blocks:
    #    print "[%d -- %d]" % b

def entropy(c1, c2, columns, cache={}):
    if (c1, c2) in cache:
        return cache[(c1, c2)]
    else:
        r = sum(map(lambda x, y: abs(x-y), columns[c1], columns[c2]))
        cache[(c1, c2)] = r
        return r

def image_entropy(blocks, columns):
    return sum(map(lambda x, y: entropy(x[1], y[0], columns), blocks[:-1], blocks[1:]))

def merge(blocks, bw, w):
    columns = [bw[i::w] for i in range(0, w)]

    
    while len(blocks) > 1:
        entropy_matrix = {}
        for i, b1 in enumerate(blocks):
            for j, b2 in enumerate(blocks):
                if not i == j:
                    entropy_matrix[(i,j)] = entropy(b1['end'], b2['start'], columns)

        ((i, j), e) = min(entropy_matrix.items(), key=lambda x: x[1])
        b1 = blocks[i]
        b2 = blocks[j]

        pprint(b1)
        pprint(b2)
        print e, entropy(b1['end'], b2['start'], columns)

        new_block = {'start':b1['start'], 'end':b2['end'], 'parts': b1['parts']+b2['parts']}

        if i < j:
            del blocks[j]
            del blocks[i]
        else:
            del blocks[i]
            del blocks[j]

        blocks.append(new_block)
    return blocks[0]
        
 


def sort(blocks, bw, w):
    columns = [bw[i::w] for i in range(0, w)]
    print "starting sort"

    for i in range(len(blocks)):
        first = blocks[i]
        #first_next = blocks[i]

        for j in range(len(blocks)-1):
            second = blocks[j]
            #second_next = blocks[j+1]

            #status_entropy = (entropy(first[1], first_next[0], columns) +
            #                  entropy(second[1], second_next[0], columns))
            #change_entropy = (entropy(first[1], second_next[0], columns) +
            #                  entropy(second[1], first_next[0], columns))

            new_blocks = list(blocks)
            new_blocks[i] = blocks[j]
            new_blocks[j] = blocks[i]
             
            ne = image_entropy(new_blocks, columns)
            oe = image_entropy(blocks, columns)

            #print "Entropy:", ne, "<", oe

            if ne < oe:
                print "Switching", first, "with", second
                blocks = new_blocks
                #print "Old entropy", (origin[1], test[0]), old_entropy
                #print "New entropy", (new[1], test[0]), new_entropy
                #blocks[i] = second
                #blocks[j] = first
                return sort(blocks, bw, w)
    print blocks


def gess_dividers(bw, w, h):

    
    diff = map(lambda x, y: abs(x-y), bw, bw[1:]+[0])
    avg = sum(diff)/len(diff)
    diff_image = Image.new('L', (w, h))
    diff_image.putdata(tuple(diff))
    diff_image.save('test.png')

    columns = map(lambda i: diff[i::w], range(w))
    columns = map(lambda a: reduce(lambda x, y: x+1 if y > avg else x, a, 0), columns)

    diff_columns = map(lambda x, y: abs(x-y), [0] + columns[:-1], columns)

    dividers = []
    for i in range(1, len(diff_columns)):
        p,v = diff_columns[i-1:i+1]
        if v > p and v > 30:
            dividers.append(i+1)
            #print "%d: %d" % (i, v)

    blocks = map(lambda x, y: {'start': x, 'end': y-1, 'parts':[(x, y-1)]}, [0]+dividers[:-1], dividers)
    return blocks
    #most_likely_values(dividers[:-1], bw, w)




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
    w,h = img.size
    data = img.getdata()

    bw = map(sum, data)

    #blocks = gess_dividers(bw, w, h)
    dividers = range(0, w, 32)
    blocks = map(lambda x, y: {'start': x, 'end': y-1, 'parts':[(x, y-1)]}, dividers, dividers[1:]+[640])
    pprint(blocks)
    
    r = merge(blocks, bw, w)

    data = list(data)
    image_columns = map(lambda i: data[i::w], range(w))

    unshredded_columns = []
    for p in r['parts']:
        init = p[0]
        end = p[1]
        unshredded_columns += image_columns[init:end+1]

    newdata = []
    
    print len(unshredded_columns)
    print len(unshredded_columns[0])

    for j in range(h):
        for i in range(w):
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
