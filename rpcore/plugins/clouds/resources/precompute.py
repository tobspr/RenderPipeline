
import noise
from panda3d.core import PNMImage

SEED = 123.0

img = PNMImage(128, 128, 3)

print("Computing 2d noise ..")
scale = 7.0
for x in range(128):
    for y in range(128):
        colors = []
        for c in range(3):
            colors.append(noise.snoise2(x / 128.0 * scale, y / 128.0 * scale, octaves=2,
                repeatx=scale, repeaty=scale, base=SEED + 362.9241 * c))
        img.set_xel(x, y, *(i*0.5+0.5 for i in colors))

img.write("tex_2d_1.png")


img = PNMImage(32 * 8, 32 * 4, 3)
scale = 4

print("Computing 3d noise .. # 1")
for z in range(32):
    x_offs = (z % 8) * 32
    y_offs = (z / 8) * 32
    for x in range(32):
        for y in range(32):
            result = noise.pnoise3(x / 32.0 * scale, y / 32.0 * scale , z / 32.0 * scale, octaves=6, repeatx=scale, repeaty=scale, repeatz=scale, base=1353 + int(SEED))
            img.set_xel(x_offs + x, y_offs + y, result * 0.5 + 0.5)

img.write("tex_3d_2.png")


img = PNMImage(128 * 16, 128 * 8, 3)
scale = 4
print("Computing 3d noise .. # 2")

for z in range(128):
    x_offs = (z % 16) * 128
    y_offs = (z / 16) * 128
    for x in range(128):
        for y in range(128):
            result = noise.pnoise3(x / 128.0 * scale, y / 128.0 * scale , z / 128.0 * scale, octaves=5, repeatx=scale, repeaty=scale, repeatz=scale, base=2 + int(SEED / 10.0))
            img.set_xel(x_offs + x, y_offs + y, result * 0.5 + 0.5)

img.write("tex_3d_1.png")
