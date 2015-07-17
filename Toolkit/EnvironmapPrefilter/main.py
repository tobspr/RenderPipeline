

# Adjust to your needs
src = "source/#.png"



import sys
sys.path.insert(0, "../../")

from Code.RenderTarget import RenderTarget
from Code.Globals import Globals
from panda3d.core import *


loadPrcFileData("", "gl-cube-map-seamless #t")
loadPrcFileData("", "show-frame-rate-meter #t")
loadPrcFileData("", "win-size 100 100")

import direct.directbase.DirectStart
Globals.load(base)

base.bufferViewer.toggleEnable()


envmap = loader.loadCubeMap(src)
envmap.setMinfilter(Texture.FTLinear)
envmap.setMagfilter(Texture.FTLinear)
envmap.setFormat(Texture.FRgb)


vertexShader = """
#version 400

uniform mat4 p3d_ModelViewProjectionMatrix;

in vec4 p3d_Vertex;
out vec2 texcoord;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    texcoord =  sign(p3d_Vertex.xz * 0.5 + 0.5);
}

"""

fragmentShader = """
#version 400




vec2 poissonDisk136[136] = vec2[](
vec2(-0.6697026f, 0.252588f),
vec2(-0.7525879f, 0.3569039f),
vec2(-0.5886698f, 0.0613417f),
vec2(-0.7174631f, -0.0006270428f),
vec2(-0.5572512f, 0.3244295f),
vec2(-0.896819f, 0.3773167f),
vec2(-0.860422f, 0.2147603f),
vec2(-0.5219118f, 0.1844902f),
vec2(-0.8549935f, 0.07924795f),
vec2(-0.5992872f, 0.4947444f),
vec2(-0.7355302f, 0.1317244f),
vec2(-0.8059348f, 0.4936432f),
vec2(-0.9957034f, 0.03100778f),
vec2(-0.4535693f, -0.1234295f),
vec2(-0.3522737f, 0.1163739f),
vec2(-0.5881585f, -0.1119891f),
vec2(-0.4566478f, 0.02817134f),
vec2(-0.6913785f, -0.1998049f),
vec2(-0.9067419f, -0.1753786f),
vec2(-0.5298578f, -0.2660885f),
vec2(-0.596201f, -0.4078353f),
vec2(-0.7809454f, -0.312936f),
vec2(-0.7302396f, -0.4471018f),
vec2(-0.2852859f, -0.03160182f),
vec2(-0.3990437f, 0.25489f),
vec2(-0.216252f, 0.0897238f),
vec2(-0.3566286f, -0.3364299f),
vec2(-0.4494278f, -0.4962978f),
vec2(-0.2808571f, -0.2060643f),
vec2(-0.7303981f, 0.6070479f),
vec2(-0.3594226f, 0.4166711f),
vec2(-0.4283986f, 0.5403531f),
vec2(-0.8934875f, -0.4217622f),
vec2(-0.3371144f, 0.7255364f),
vec2(-0.5394667f, 0.6111398f),
vec2(-0.2614467f, 0.5158143f),
vec2(-0.4977357f, 0.7883558f),
vec2(-0.4718757f, -0.6901266f),
vec2(-0.2635473f, -0.5040556f),
vec2(-0.3197165f, -0.6472418f),
vec2(-0.6292481f, -0.5883422f),
vec2(-0.6396437f, 0.7053597f),
vec2(-0.07929505f, -0.1198472f),
vec2(-0.0684788f, 0.01391225f),
vec2(-0.2670797f, 0.2169997f),
vec2(-0.2191026f, 0.9015591f),
vec2(-0.08619704f, 0.7675754f),
vec2(-0.1929925f, 0.6797483f),
vec2(-0.4013852f, 0.8863319f),
vec2(-0.3989866f, -0.9094133f),
vec2(-0.5240726f, -0.8301671f),
vec2(-0.2598244f, -0.8106751f),
vec2(-0.6597859f, -0.7325349f),
vec2(0.06070184f, -0.1665733f),
vec2(0.1479672f, -0.02537431f),
vec2(0.0170486f, -0.2923723f),
vec2(-0.1398243f, -0.2555625f),
vec2(0.05607247f, 0.08279747f),
vec2(-0.1096114f, 0.3267188f),
vec2(-0.05517402f, 0.2035471f),
vec2(-0.1943692f, -0.9595839f),
vec2(-0.1218549f, -0.6139406f),
vec2(-0.06455816f, -0.9481208f),
vec2(-0.1256548f, -0.7920513f),
vec2(-0.8191254f, -0.5493588f),
vec2(-0.2185396f, -0.3729787f),
vec2(-0.1076538f, 0.4597256f),
vec2(-0.2392801f, 0.3571682f),
vec2(-0.8494083f, -0.05481881f),
vec2(-0.04855901f, 0.9368494f),
vec2(0.1445959f, 0.2432573f),
vec2(0.05332827f, 0.3799112f),
vec2(0.1954546f, -0.2597516f),
vec2(0.2904174f, -0.1362483f),
vec2(0.3162677f, 0.1174763f),
vec2(0.3746301f, -0.02258325f),
vec2(0.09393504f, -0.8414481f),
vec2(0.108514f, -0.9930339f),
vec2(0.04650671f, -0.7145066f),
vec2(0.4245852f, 0.2855053f),
vec2(0.4909475f, 0.1163015f),
vec2(0.2713183f, 0.3049493f),
vec2(0.08440985f, 0.7562921f),
vec2(0.0735344f, 0.5881544f),
vec2(0.09105957f, 0.9377573f),
vec2(-0.06067296f, 0.6040952f),
vec2(-0.06186697f, -0.4719045f),
vec2(0.2385143f, 0.7563667f),
vec2(0.3044139f, 0.4959942f),
vec2(0.1714154f, 0.4406541f),
vec2(0.3101307f, 0.6402999f),
vec2(0.4362539f, 0.4436178f),
vec2(0.1855191f, 0.1075504f),
vec2(0.4228271f, 0.71344f),
vec2(0.5632554f, 0.4815079f),
vec2(0.4683265f, 0.5748566f),
vec2(0.5852427f, -0.06538045f),
vec2(0.6286269f, 0.2729764f),
vec2(0.6378487f, 0.06608652f),
vec2(0.7355191f, 0.1873053f),
vec2(0.4597037f, -0.1220558f),
vec2(0.05372116f, -0.5717897f),
vec2(0.1334148f, -0.3839873f),
vec2(0.802549f, 0.001696069f),
vec2(0.7448433f, -0.1381802f),
vec2(0.8731436f, 0.1137444f),
vec2(0.6083444f, 0.6262938f),
vec2(0.2272874f, 0.9104604f),
vec2(0.6975611f, 0.4005116f),
vec2(0.8100093f, 0.5314193f),
vec2(0.8722062f, -0.2156337f),
vec2(0.9825792f, -0.1071116f),
vec2(0.8207953f, -0.3714042f),
vec2(0.6157539f, -0.1920788f),
vec2(0.6425018f, -0.3308856f),
vec2(0.8562624f, 0.3125054f),
vec2(0.4221315f, 0.865036f),
vec2(0.2771236f, -0.455153f),
vec2(0.2075053f, -0.6301893f),
vec2(0.3261909f, -0.2738115f),
vec2(0.2636439f, -0.8120635f),
vec2(0.4209208f, -0.6943635f),
vec2(0.3391235f, -0.5921174f),
vec2(0.9905176f, 0.03439083f),
vec2(0.7413607f, 0.6599857f),
vec2(0.3959692f, -0.8634195f),
vec2(0.5840687f, 0.7631645f),
vec2(0.5299603f, -0.4261315f),
vec2(0.4914075f, -0.2812121f),
vec2(0.2420735f, -0.9424312f),
vec2(0.7644672f, -0.5535595f),
vec2(0.6224207f, -0.580614f),
vec2(0.3979274f, -0.4027851f),
vec2(0.7203274f, -0.6829374f),
vec2(0.5771253f, -0.7289275f),
vec2(0.4877075f, -0.5674056f)
);

in vec2 texcoord;
out vec4 resultColor;

uniform samplerCube sourceMap;
uniform int directionIndex;
uniform int mipIndex;
uniform float blurFactor;

vec3 transformCubemapCoordinates(vec3 coord) {
    return normalize(coord.xzy * vec3(1,-1,1));
    //return normalize(coord);
}

vec3 getTransformedCoord(vec2 coord) {
    if (directionIndex == 1) return vec3(-1, coord); 
    if (directionIndex == 2) return vec3(coord, -1);
    if (directionIndex == 0) return vec3(1, -coord.x, coord.y);
    if (directionIndex == 3) return vec3(coord.xy * vec2(1,-1), 1);
    if (directionIndex == 4) return vec3(coord.x, 1, coord.y);
    if (directionIndex == 5) return vec3(-coord.x, -1, coord.y);
    return vec3(0);
}



void main() {
    
    vec2 scaledCoord = texcoord * 2.0 - 1.0;
    vec3 direction = transformCubemapCoordinates(getTransformedCoord(scaledCoord));

    vec3 sum = vec3(0);
    float factorSum = 0.0;

    for (int i = 0; i < 136; i++) {
        vec2 coordOffs = poissonDisk136[i] * 0.04 * blurFactor;
        vec3 lookupDir = transformCubemapCoordinates(getTransformedCoord(scaledCoord + coordOffs));
        float factor = 1.0 - clamp(length(coordOffs), 0.0, 1.0);
        sum += texture(sourceMap, lookupDir).xyz * factor;
        factorSum += factor;
    }
    sum /= factorSum;

    // vec3 cubeColor = texture(sourceMap, direction).xyz;

    resultColor = vec4(sum, 1);

}
"""
shader = Shader.make(Shader.SLGLSL, vertexShader, fragmentShader)





size = 1024
mipidx = 0
blurF = 0.5
while size > 1:
    size /= 2
    blurF *= 1.5

    target = RenderTarget("precompute cubemap")
    target.addColorTexture()
    target.setSize(size, size)
    target.prepareOffscreenBuffer()

    stex = target.getColorTexture()

    target.setShader(shader)
    target.setShaderInput("sourceMap", envmap)
    target.setShaderInput("mipIndex", mipidx)
    target.setShaderInput("blurFactor", blurF)

    for i in xrange(6):

        print "Generating face", i,"for mipmap",mipidx
        target.setShaderInput("directionIndex", i)
        base.graphicsEngine.renderFrame()
        base.graphicsEngine.extractTextureData(stex, base.win.getGsg())

        stex.write("result/" + str(mipidx) + "_" + str(i) + ".png")

    target.deleteBuffer()
    mipidx += 1

# run()
