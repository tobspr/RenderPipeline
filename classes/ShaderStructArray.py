
from DebugObject import DebugObject
from panda3d.core import Mat4, NodePath

class ShaderStructArray(DebugObject):
    
    def __init__(self, classType, numElements):
        DebugObject.__init__(self, "ShaderStructArray")

        self.debug("Init shaderStructArray of size",numElements,"from",classType)
        self.classType = classType
        self.attributes = classType.getExposedAttributes()
        
        self.debug("Attributes found:", self.attributes)

        self.size = numElements
        self.parents = {}

    def bindTo(self, parent, uniformName):
        self.parents[parent] = uniformName 


        for index in xrange(self.size):
            for attrName, attrType in self.attributes.items():
                inputName = uniformName + "[" + str(index) + "" "]" + "." + attrName

                if attrType == "mat4":
                    inputValue = self._convertValue(Mat4())
                else:
                    inputValue = self._convertValue(0.0)
                parent.setShaderInput(inputName, inputValue)


    def _convertValue(self, val):
        if type(val) == Mat4:
            tmp = NodePath("tmp")
            tmp.setMat(val)
            return tmp

        return val


    def __setitem__(self, index, value):
        index = int(index)

        for attrName in self.attributes.keys():

            for parent, uniformName in self.parents.items():
                inputName = uniformName + "[" + str(index) + "" "]" + "." + attrName
                inputValue = self._convertValue(getattr(value, attrName))
                parent.setShaderInput(inputName, inputValue)

        # for key in self.attributes.keys():
        #     self.rawArrays[key][index] = getattr(value, key)
