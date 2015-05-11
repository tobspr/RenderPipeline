
from DebugObject import DebugObject
from panda3d.core import PTAInt, PTAFloat, PTAMat4
from panda3d.core import PTALVecBase2f, PTALVecBase3f
from panda3d.core import PStatCollector

pstats_SetShaderInputs = PStatCollector("App:ShaderStructArray:SetShaderInputs")


class ShaderStructArray(DebugObject):

    AllArrays = []

    """ This class provides the ability to pass python lists as shader inputs, 
    as panda3d lacks this feature (yet). The items are set with the [] operator.

    NOTICE: the the shader inputs for an object are only refreshed
    when using the [] operator. So whenever you change a property
    of an object, you have to call myShaderStructArray[index] = Object,
    regardless wheter the object is already in the list or not.
    EDIT: The object itself can also call onPropertyChanged() to force
    an update. Notice, that everytime this function is called, the
    shader-inputs are refeshed for that object. You should probably only
    call this once per frame.

    For further information about accessing the data in your shaders, see
    bindTo().

    Todo: Make the exposed types more generic. See getExposedAttributes in
    ShaderStructElement.
    """

    def __init__(self, classType, arraySize):
        """ Constructs a new array, containing elements of classType and
        with the size of numElements. classType and arraySize can't be
        changed after initialization """

        DebugObject.__init__(self, "ShaderStructArray")

        self.arrayIndex = len(self.AllArrays)
        self.AllArrays.append(self)


        self.classType = classType
        self.attributes = classType.getExposedAttributes()

        self.size = arraySize
        self.parents = {}
        self.ptaWrappers = {}
        self.assignedObjects = [None for i in range(arraySize)]

        componentSize = 0

        for name, attrType in self.attributes.iteritems():
            arrayType = PTAFloat
            numElements = 1
            numFloats = 1

            if attrType == "mat4":
                arrayType = PTAMat4
                numFloats = 16

            elif attrType == "int":
                arrayType = PTAInt
                numFloats = 1

            # hacky, but works, will get replaced later by a parser
            elif attrType == "array<int>(6)":
                arrayType = PTAInt
                numElements = 6
                numFloats = 6

            elif attrType == "float":
                arrayType = PTAFloat
                numFloats = 1

            elif attrType == "vec2":
                arrayType = PTALVecBase2f
                numFloats = 2

            elif attrType == "vec3":
                arrayType = PTALVecBase3f
                numFloats = 3

            componentSize += numFloats
            self.ptaWrappers[name] = [
                arrayType.emptyArray(numElements) for i in range(self.size)]

        self.debug("Init array, size =", self.size,"floats=",componentSize,"total =",self.size * componentSize)

    def getUID(self):
        """ Returns the unique index of this array """
        return self.arrayIndex

    def objectChanged(self, obj, index):
        """ A list object calls this when it changed. Do not call this
        directly """

        self._rebindInputs(index, obj)

    def _rebindInputs(self, index, value):
        """ Rebinds the shader inputs for an index """
        pstats_SetShaderInputs.start()
        for attrName, attrType in self.attributes.iteritems():
            objValue = getattr(value, attrName)
            # # Cast values to correct types
            # if attrType == "float":
            #     objValue = float(objValue)
            # elif attrType == "int":
            #     objValue = int(objValue)
            if attrType == "array<int>(6)":
                for i in range(6):
                    self.ptaWrappers[attrName][index][i] = objValue[i]
            else:
                # print attrName, objValue
                self.ptaWrappers[attrName][index][0] = objValue
            # elif attrType == "mat4":
            #     self.ptaWrappers[attrName][index][0] = objValue
            # else:
        pstats_SetShaderInputs.stop()

    def __setitem__(self, index, value):
        """ Sets the object at index to value. This directly updates the
        shader inputs. """

        if index < 0 or index >= self.size:
            raise Exception("Out of bounds!")

        oldObject = self.assignedObjects[index]

        # Remove old reference
        if value is not None and oldObject is not None \
                and oldObject is not value:
            self.assignedObjects[index].removeListReference(self.arrayIndex)

        # Set new reference
        value.assignListIndex(self.arrayIndex, index)
        self.assignedObjects[index] = value
        self._rebindInputs(index, value)

    def bindTo(self, parent, uniformName):
        """ In order for an element to recieve this array as an
        shader input, you have to call bindTo(object, uniformName). The data
        will then be available as uniform with the name uniformName in the
        shader. You still have to define a structure in your shader which has
        the same properties than your objects. As example, if you have the
        following class:

            class Light(ShaderStructElement):
                def __init__(self):
                    ShaderStructElement.__init__(self)
                    self.color = Vec3(1)

                @classmethod
                def getExposedAttributes(self):
                    return {
                        "color": "vec3"
                    }

        you have to define the following structure in your shader:

            struct Light {
                vec3 color;
            }

        and declare the uniform input as:

            uniform Light uniformName[size]

        You can then access the data as with any other uniform input.
        """       
        self.parents[parent] = uniformName

        for index in range(min(999, self.size) ):
            for attrName, attrType in self.attributes.iteritems():
                inputName = uniformName + \
                    "[" + str(index) + "" "]" + "." + attrName
                inputValue = self.ptaWrappers[attrName][index]

                parent.setShaderInput(inputName, inputValue)



class ShaderStructElement:

    """
    This is the abstract parent class for all classes which can be attached to
    a ShaderStructArray. Each class should override the getExposedAttributes()
    method to tell the array which data layout it has.

    Whenever a property got changed, the class should call onPropertyChanged()
    to tell the ShaderStructArray that its values should get passed to the
    shader again.

    """

    @classmethod
    def getExposedAttributes(self):
        """ Subclasses should implement this method, and return a
        dictionary of values to expose to the shader. A sample
        return value might be:

        return {
            "someVector": "vec3",
            "someColor": "vec3",
            "someInt": "int",
            "someFloat": "float",
            "someArray": "array<int>(6)",
        }

        All keys have to be a property of the subclass. Arrays
        have to be a PTAxxx, e.g. PTAInt for an int array.

        NOTICE: Currently only int arrays of size 6 are supported, until
        I implement a more generic system. """

        raise NotImplementedError()

    def __init__(self):
        """ Constructor, creates the list of referenced lists """
        self.referencedListsIndices = {}

    def onPropertyChanged(self):
        """ This method should be called by the class instance itself
        whenever it modified an exposed value """
        for structArrayIndex, elementIndex in self.referencedListsIndices.iteritems():
            ShaderStructArray.AllArrays[structArrayIndex].objectChanged(self, elementIndex)

    def assignListIndex(self, structArrayIndex, index):
        """ A struct array calls this when this object is contained
        in the array. """
        self.referencedListsIndices[structArrayIndex] = index

    def removeListReference(self, structArrayIndex):
        """ A struct array calls this when this object got deleted from
        the list, e.g. by assigning another object at that index """
        if structArrayIndex in self.referencedListsIndices:
            del self.referencedListsIndices[structArrayIndex]

