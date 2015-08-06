

# First, we have to insert the pipeline path to the python path
import sys
# sys.path.insert(0, '../../RenderPipeline')

# Now import the pipeline
from Code.RenderingPipeline import RenderingPipeline

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile, Vec3, Texture, OmniBoundingVolume
from Code.PointLight import PointLight
from Code.DirectionalLight import DirectionalLight
from random import random
from math import sin , cos , acos , degrees , atan
# Create a showbase class
class App(ShowBase):

    def __init__(self):

        # Load the default configuration.prc. This is recommended, as it
        # contains some important panda options
        loadPrcFile("Config/configuration.prc")

        # Init the showbase
        ShowBase.__init__(self)

        # Create a new pipeline instance
        self.renderPipeline = RenderingPipeline(self)

        # Set the base path for the pipeline. This is required as we are in
        # a subdirectory
        self.renderPipeline.getMountManager().setBasePath(".")

        # Also set the write path
        self.renderPipeline.getMountManager().setWritePath("Temp/")

        # Load the default settings
        self.renderPipeline.loadSettings("Config/pipeline.ini")

        # Now create the pipeline
        self.renderPipeline.create()

        # Load the skybox
        self.skybox = self.renderPipeline.getDefaultSkybox()
        self.skybox.reparentTo(render)



        # At this point we are done with the initialization. Now you want to
        # load your scene, and create the game logic. 

        # Call this to tell the pipeline that the scene is done loading
       
    
        
        for x in range(1):
            self.tree = loader.loadModel("Demoscene.ignore/Treemodel/testtree3.egg")
            for y in self.tree.findAllTextures():
                #print y , dir(Texture)
                if "tex/diffuse.tga" in str(y.getFullpath()):
                    y.setFormat(Texture.FSrgbAlpha)
                if "tileable_tree_bark_ftourini.jpg" in str(y.getFullpath()):
                    y.setFormat(Texture.FSrgb)
            self.tree.reparentTo(render)
            self.tree.setH(random()*360)
            self.tree.setX(random()*10*4)
            self.tree.setY(random()*10*4)
            self.tree.setScale(1+0.15*random())
            self.tree.setTwoSided(True)
            self.tree.setInstanceCount(100 * 100)
            self.tree.setShaderInput("numInstanceRows", 100)
            self.renderPipeline.setEffect(self.tree, "Effects/ExampleTreeInstanced.effect", {
                "alphaTest": True
            })
            self.tree.node().setFinal(True)
            self.tree.node().setBounds(OmniBoundingVolume())
            # self.weed.setTransparency(True)
        
        #lerpival = self.weed.hprInterval(20, Vec3(360, 0, 0))
        #lerpival.loop()
        
        dPos = Vec3(60, 30, 100)*100000
        dirLight = DirectionalLight()
        #dirLight.setDirection(dPos)
        dirLight.setShadowMapResolution(1024)
        dirLight.setPos(dPos)
        dirLight.setColor(Vec3(1.5, 1.2, 0.8))
        # dirLight.setColor(Vec3(0.3))
        dirLight.setPssmTarget(base.cam, base.camLens)
        dirLight.setCastsShadows(True)
        dirLight.setPssmDistance(50)
        self.renderPipeline.addLight(dirLight)
        self.dirLight = dirLight
        sunPos = Vec3(56.7587, -31.3601, 189.196)*100000
        self.renderPipeline.setScatteringSource(dirLight)
        #self.dirLight.setPos(sunPos)
        #self.dirLight.setDirection(sunPos)
        # Tell the GI which light casts the GI

        '''
        sampleLight = PointLight() 
        sampleLight.setRadius(400.0)
        sampleLight.setColor(Vec3(1))
        sampleLight.setPos(Vec3(10,10,10))
        self.renderPipeline.addLight(sampleLight)
        ''' 
        self.loadHarvester()
        self.renderPipeline.onSceneInitialized()
        taskMgr.add(self.animCrane, 'updateWorld')

    def animCrane(self,task):
        t = task.time

        # import time
        # time.sleep(0.1)
        
        for x in self.harvesterparts["wheels"]:
            x.setP(t*360/5)
        
        #self.harvesterparts["el_0"].setH(cos(t*3.14/10)*100) #+-100 deg
        
        z = self.harvesterparts["endpoint"].getZ(self.harvesterparts["el_0"])+1
        angle = self.harvesterparts["el_1"].getP() 
        
        angle += z*2 #instabilty somewhere between 10 and 20, depends on fps tho
            
        angle = max(30,min(angle,100))
        #angle = cos(t*3.14/10)*35+65 # 30 to 100?
        
        self.harvesterparts["el_1"].setP(angle) # 30 to 100?
        # print angle,z
        self.harvesterparts["piston1-A"].lookAt(self.harvesterparts["piston1-B"])
        self.harvesterparts["piston1-B"].lookAt(self.harvesterparts["piston1-A"])
        
        ### set the upper angle, do trigonomic math to calculate all mechanical elements positions on the arm.
         #-60 +220
        angle =  cos(t*3.14/10)*55 -285 #230-340
        #print angle
        self.harvesterparts["el_3"].setP( angle) #-60 -210 deg -190 -355
        #self.harvesterparts["el_2"].setP( cos(t*3.14/10)*25 +15) #-10 +40 deg #debug only,angle is driven later
        self.harvesterparts["piston2-A"].lookAt(self.harvesterparts["piston2-B"])
        self.harvesterparts["piston2-B"].lookAt(self.harvesterparts["piston2-A"])
        
        #rotate upper joints
        a = self.harvesterparts["el_6"].getDistance(self.harvesterparts["el_5t"])
        b = self.harvesterparts["el_5"].getDistance(self.harvesterparts["el_6t"])
        c = self.harvesterparts["el_5"].getDistance(self.harvesterparts["el_6"])
        alpha = degrees(acos((b*b+c*c-a*a)/(2*b*c)))
        betha = degrees(acos((a*a+c*c-b*b)/(2*a*c)))
        gamma = 180-betha-alpha
        
        
        #print a,b,c, alpha,betha,gamma
        self.harvesterparts["el_6"].lookAt(self.harvesterparts["el_5"],(0,0,0),(0,0,1))
        self.harvesterparts["el_5"].lookAt(self.harvesterparts["el_6"],(0,0,0),(0,0,1))

        self.harvesterparts["el_5"].setHpr(self.harvesterparts["el_5"],0,betha,0)
        self.harvesterparts["el_6"].setHpr(self.harvesterparts["el_6"],0,-alpha,0)
        
        #rotate lower joints
        
        x,y,z = self.harvesterparts["el_7"].getPos(self.harvesterparts["el_2"])
        
        alpha2 = degrees(atan(-z/y )) #angle from el2 to el7 (in el2 coords) !!not quite correct!
        a = self.harvesterparts["el_2"].getDistance(self.harvesterparts["el_7t"])
        b = self.harvesterparts["el_7"].getDistance(self.harvesterparts["el_7l"])
        c = self.harvesterparts["el_2"].getDistance(self.harvesterparts["el_7"])
        alpha = degrees(acos((b*b+c*c-a*a)/(2*b*c)))
        betha = degrees(acos((a*a+c*c-b*b)/(2*a*c)))
        gamma = 180-betha-alpha
        #print alpha, betha , gamma,alpha2
        
        self.harvesterparts["el_2"].setHpr(0,betha+alpha2,0)
        
        self.harvesterparts["el_7"].lookAt(self.harvesterparts["el_7t"],(0,0,0),(0,0,1))
        
        ### end of joint's parametrical movement
        
        dist = cos(t*3.14/30)*1.25 +1.25
        self.harvesterparts["el_4"].setY(dist)
        
        #print self.harvesterparts["el_7t"].getDistance(self.harvesterparts["el_7l"])
        
        """
        self.harvesterparts["el_6"].setHpr(0,40,0)
        if self.harvesterparts["el_3"].getP()<-140 :
            self.harvesterparts["el_5"].setHpr(0,180,0)
        else:
            self.harvesterparts["el_5"].setHpr(0,100,0)

        for x in range(1): #itteration to find equilibrium for the mechanics

            self.harvesterparts["el_5"].lookAt(self.harvesterparts["el_5t"],(0,0,0),(-1,0,0))
            #self.harvesterparts["el_5"].setH(0)
            #self.harvesterparts["el_5"].setR(0)
            self.harvesterparts["el_6"].lookAt(self.harvesterparts["el_6t"],(0,0,0),(0,-1,0))
            #self.harvesterparts["el_6"].setH(0)
            #self.harvesterparts["el_6"].setR(0)
        """
        #self.harvesterparts["el_6"].setH(0)
        #self.harvesterparts["el_6"].setR(0)
        #self.harvesterparts["el_5"].setH(0)
        #self.harvesterparts["el_5"].setR(0)
        
        
        """
        lerpival =  self.harvesterparts["el_1"].hprInterval(20, Vec3(360, 0, 0))
        lerpival.loop()
        
        for x in self.harvesterparts["wheels"]:
            lerpival =  x.hprInterval(20, Vec3(0, 360, 0))
            lerpival.loop()
        """
        return task.cont
        
    def loadHarvester(self):
        self.harvester = loader.loadModel("Demoscene.ignore/HarvesterModel/Model.egg")
        self.harvester.reparentTo(render)
        self.renderPipeline.setEffect(self.harvester, "Effects/Default/Default.effect", {
                "dynamic": True
            })
        # print self.harvester.ls()
        
        self.harvesterparts = {
        "wheels":self.harvester.findAllMatches("**/hub_**"),
        "el_0":self.harvester.find("**/crane_element_0"),
        "el_1":self.harvester.find("**/crane_element_1"),
        "el_2":self.harvester.find("**/crane_element_2"),
        "el_3":self.harvester.find("**/crane_element_3"),
        "el_4":self.harvester.find("**/crane_element_4"),
        "el_5":self.harvester.find("**/crane_element_5"),
        "el_6":self.harvester.find("**/crane_element_6"),
        "el_7":self.harvester.find("**/crane_element_7"),
        "el_5t":self.harvester.find("**/crane_element_5_target"),
        "el_6t":self.harvester.find("**/crane_element_6_target"),
        "el_7t":self.harvester.find("**/crane_element_7_target"),
        "el_7l":self.harvester.find("**/crane_element_7_len"),
        "endpoint":self.harvester.find("**/crane_element_4_endpoint"),
        "piston1-A":self.harvester.find("**/piston1-A"),
        "piston1-B":self.harvester.find("**/piston1-B"),
        "piston2-A":self.harvester.find("**/piston2-A"),
        "piston2-B":self.harvester.find("**/piston2-B"),
        
        }
        
        
        
    
# Create a new instance and run forever
app = App()
app.run()
