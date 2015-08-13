
from DebugObject import DebugObject


from RenderPasses.SSLRPass import SSLRPass


class SSLRManager(DebugObject):

    """ This manager handles the Screen Space Local Techniques feature. """

    def __init__(self, pipeline):
        DebugObject.__init__(self, "SSLRManager")

        self.pipeline = pipeline

        # Add SSLR pass
        if self.pipeline.settings.enableSSLR:
            self.sslrPass = SSLRPass()
            self.sslrPass.setHalfRes(self.pipeline.settings.sslrUseHalfRes)
            self.pipeline.renderPassManager.registerPass(self.sslrPass)

            self.pipeline.renderPassManager.registerDefine("USE_SSLR", 1)

        if self.pipeline.settings.sslrUseHalfRes:
            self.pipeline.renderPassManager.registerDefine("SSLR_HALF_RES", 1)
            
        self.pipeline.renderPassManager.registerDefine("SSLR_STEPS", 
            self.pipeline.settings.sslrNumSteps)
        self.pipeline.renderPassManager.registerDefine("SSLR_SCREEN_RADIUS", 
            self.pipeline.settings.sslrScreenRadius)


    def update(self):
        pass