
from panda3d.core import SamplerState, Texture, CardMaker, TransparencyAttrib
from panda3d.core import Camera, NodePath, OmniBoundingVolume, BitMask32, Vec4

from .. import *


class CloudStage(RenderStage):

    """ This stage handles the volumetric cloud rendering """

    required_pipes = ["ShadedScene", "GBuffer", "ScatteringCubemap"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "CloudStage", pipeline)
        self._voxel_res_xy = 512
        self._voxel_res_z = 32
        self._sprite_tex = None

    def set_sprites(self, sprite_tex):
        self._sprite_tex = sprite_tex

    def get_produced_pipes(self):
        return {"ShadedScene": self._target_apply_clouds["color"]}

    def get_produced_defines(self):
        return {
            "CLOUD_RES_XY": self._voxel_res_xy,
            "CLOUD_RES_Z": self._voxel_res_z
        }

    def create(self):

        # Construct the voxel texture
        self._cloud_voxels = Image.create_3d("CloudVoxels", self._voxel_res_xy, self._voxel_res_xy, self._voxel_res_z,
            Texture.T_unsigned_byte, Texture.F_rgba8)
        self._cloud_voxels.get_texture().set_wrap_u(SamplerState.WM_repeat)
        self._cloud_voxels.get_texture().set_wrap_v(SamplerState.WM_repeat)
        self._cloud_voxels.get_texture().set_wrap_w(SamplerState.WM_border_color)
        self._cloud_voxels.get_texture().set_border_color(Vec4(0, 0, 0, 0))
        # self._cloud_voxels.get_texture().set_border_color(Vec4(1, 0, 0, 1))

        # Construct the target which populates the voxel texture
        self._grid_target = self._create_target("Clouds:CreateGrid")
        self._grid_target.set_size(self._voxel_res_xy, self._voxel_res_xy)
        self._grid_target.prepare_offscreen_buffer()
        self._grid_target.set_shader_input("CloudVoxels", self._cloud_voxels.get_texture())

        # Construct the target which shades the voxels
        self._shade_target = self._create_target("Clouds:ShadeVoxels")
        self._shade_target.set_size(self._voxel_res_xy, self._voxel_res_xy)
        self._shade_target.prepare_offscreen_buffer()
        self._shade_target.set_shader_input("CloudVoxels", self._cloud_voxels.get_texture())
        self._shade_target.set_shader_input("CloudVoxelsDest", self._cloud_voxels.get_texture())

        self._particle_target = self._create_target("Clouds:RenderClouds")
        self._particle_target.set_half_resolution()
        self._particle_target.add_color_texture(bits=16)
        self._particle_target.prepare_offscreen_buffer()
        self._particle_target.set_shader_input("CloudVoxels", self._cloud_voxels.get_texture())

        # self._make_particle_scene()

        self._target_apply_clouds = self._create_target("Clouds:ApplyClouds")
        self._target_apply_clouds.add_color_texture(bits=16)
        self._target_apply_clouds.prepare_offscreen_buffer()

        self._target_apply_clouds.set_shader_input("CloudsTex", self._particle_target["color"])

    def _make_particle_scene(self):

        # Create a new scene root
        self._particle_scene = Globals.base.render.attach_new_node("CloudParticles")
        self._particle_scene.hide(self._pipeline.get_tag_mgr().get_gbuffer_mask())
        self._particle_scene.hide(self._pipeline.get_tag_mgr().get_shadow_mask())
        self._particle_scene.hide(self._pipeline.get_tag_mgr().get_voxelize_mask())

        cm = CardMaker("")
        cm.set_frame(-1.0, 1.0, -1.0, 1.0)
        cm.set_has_normals(False)
        cm.set_has_uvs(False)
        card_node = cm.generate()
        card_node.set_bounds(OmniBoundingVolume())
        card_node.set_final(True)
        self._particle_np = self._particle_scene.attach_new_node(card_node)
        self._particle_np.set_shader_input("SpriteTex", self._sprite_tex)
        self._particle_np.set_shader_input("CloudVoxels", self._cloud_voxels.get_texture())
        self._particle_np.set_instance_count(self._voxel_res_xy * self._voxel_res_xy * self._voxel_res_z)
        self._particle_np.set_transparency(TransparencyAttrib.M_multisample, 1000000)
        self._particle_scene.set_transparency(TransparencyAttrib.M_multisample, 1000000)

        self._particle_cam = Camera("CloudParticleCam")
        self._particle_cam.set_lens(Globals.base.camLens)
        self._particle_cam_np = self._particle_scene.attach_new_node(self._particle_cam)

        cloud_particle_mask = BitMask32.bit(16)
        self._particle_cam.set_camera_mask(cloud_particle_mask)
        render.hide(cloud_particle_mask)
        self._particle_scene.show_through(cloud_particle_mask)

        self._particle_target = self._create_target("Clouds:RenderParticles")
        self._particle_target.add_color_texture(bits=16)
        self._particle_target.set_source(self._particle_cam_np, Globals.base.win)
        self._particle_target.set_enable_transparency(True)
        self._particle_target.prepare_scene_render()
        self._particle_target.set_clear_color(True, color=Vec4(0, 0, 0, 0))

    def update(self):
        pass
    #     self._particle_cam_np.set_transform(
    #         Globals.base.camera.get_transform(Globals.base.render))

    def set_shaders(self):
        self._grid_target.set_shader(self.load_plugin_shader("GenerateClouds.frag.glsl"))
        self._target_apply_clouds.set_shader(self.load_plugin_shader("ApplyClouds.frag.glsl"))
        self._shade_target.set_shader(self.load_plugin_shader("ShadeClouds.frag.glsl"))


        self._particle_target.set_shader(self.load_plugin_shader("RenderClouds.frag.glsl"))
        # self._particle_np.set_shader(self.load_plugin_shader("CloudParticle.vert.glsl", "CloudParticle.frag.glsl"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
