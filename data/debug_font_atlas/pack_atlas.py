"""

Packs the numbers into a single atlas

"""


from panda3d.core import PNMImage

if __name__ == "__main__":

    w, h = 5, 8

    dest = PNMImage(w * 10, h, 1, 255)
    for i in range(10):
        sub = PNMImage("{}.png".format(i))
        dest.copy_sub_image(sub, i * w, 0, 0, 0, w, h)    

    dest.write("atlas.png")
