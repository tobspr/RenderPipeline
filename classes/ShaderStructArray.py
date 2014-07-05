
from DebugObject import DebugObject
from panda3d.core import Mat4, NodePath, PTAInt, PTAFloat, PTAMat4, PTALVecBase2f, PTALVecBase3f, UnalignedLMatrix4f

class ShaderStructArray(DebugObject):
    
    def __init__(self, classType, numElements):
        DebugObject.__init__(self, "ShaderStructArray")

        self.debug("Init array, size =",numElements,", from",classType)
        self.classType = classType
        self.attributes = classType.getExposedAttributes()
        
        self.size = numElements
        self.parents = {}

        self.ptaWrappers = {}

        for name, attrType in self.attributes.items():
            arrayType = PTAFloat
            numElements = 1

            if attrType == "mat4":
                arrayType = PTAMat4

            elif attrType == "int":
                arrayType = PTAInt

            # hacky, but works
            # might get replaced later
            elif attrType == "array<int>(6)":
                arrayType = PTAInt
                numElements = 6

            elif attrType == "float":
                arrayType = PTAFloat

            elif attrType == "vec2":
                arrayType = PTALVecBase2f

            elif attrType == "vec3":
                arrayType = PTALVecBase3f

            self.ptaWrappers[name] = [arrayType.emptyArray(numElements) for i in xrange(self.size)]



    def bindTo(self, parent, uniformName):
        self.parents[parent] = uniformName 

        for index in xrange(self.size):
            for attrName, attrType in self.attributes.items():
                inputName = uniformName + "[" + str(index) + "" "]" + "." + attrName
                inputValue = self.ptaWrappers[attrName][index]

                parent.setShaderInput(inputName, inputValue)

    def __setitem__(self, index, value):
        index = int(index)
        for attrName, attrType in self.attributes.items():

            objValue = getattr(value, attrName)
                       
            if attrType == "float":
                objValue = float(objValue)
            elif attrType == "int":
                objValue = int(objValue)

            if attrType == "array<int>(6)":
                for i in xrange(6):
                    self.ptaWrappers[attrName][index][i] = objValue[i] 

            elif attrType == "mat4":
                self.ptaWrappers[attrName][index][0] = objValue

            else:
                self.ptaWrappers[attrName][index][0] = objValue

            # print attrName, "->", objValue

            # for parent, uniformName in self.parents.items():
            #     inputName = uniformName + "[" + str(index) + "" "]" + "." + attrName
            #     inputValue = self._convertValue(getattr(value, attrName))
            #     parent.setShaderInput(inputName, inputValue)
                # print "setShaderInput("+str(inputName) + ",",inputValue,")"

                # print "Set shader input:",inputName, inputValue, "on",parent
