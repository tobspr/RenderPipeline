
from functools import partial

from panda3d.core import Texture, Vec3
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectScrolledFrame import DirectScrolledFrame
from direct.gui.DirectGui import DGG

from ..Util.Generic import rgb_from_string
from ..Util.DisplayShaderBuilder import DisplayShaderBuilder
from ..Globals import Globals
from ..RenderTarget import RenderTarget
from .TexturePreview import TexturePreview
from .BetterOnscreenImage import BetterOnscreenImage
from .BetterOnscreenText import BetterOnscreenText
from .DraggableWindow import DraggableWindow
from .BetterLabeledCheckbox import BetterLabeledCheckbox

class BufferViewer(DraggableWindow):

    """ This class provides a view into the buffers to inspect them """

    _REGISTERED_ENTRIES = []

    @classmethod
    def register_entry(cls, entry):
        """ Adds a new target to the registered entries """
        cls._REGISTERED_ENTRIES.append(entry)

    @classmethod
    def unregister_entry(cls, entry):
        """ Removes a target from the registered entries """
        if entry in cls._REGISTERED_ENTRIES:
            cls._REGISTERED_ENTRIES.remove(entry)

    def __init__(self, pipeline, parent):
        """ Constructs the buffer viewer """
        DraggableWindow.__init__(self, width=1400, height=800, parent=parent,
                                 title="Buffer- and Image-Browser")
        RenderTarget.RT_CREATE_HANDLER = self.register_entry
        self._pipeline = pipeline
        self._scroll_height = 3000
        self._display_images = False
        self._stages = []
        self._create_components()
        self._tex_preview = TexturePreview(self._pipeline, parent)
        self._tex_preview.hide()
        self.hide()

    def toggle(self):
        """ Updates all the buffers and then toggles the buffer viewer """
        if self._visible:
            self._remove_components()
            self.hide()
        else:
            self._perform_update()
            self.show()

    def _create_components(self):
        """ Creates the window components """
        DraggableWindow._create_components(self)

        self._content_frame = DirectScrolledFrame(
            frameSize=(0, self._width - 15, 0, self._height - 90),
            canvasSize=(0, self._width - 80, 0, self._scroll_height),
            autoHideScrollBars=False,
            scrollBarWidth=20.0,
            frameColor=(0, 0, 0, 0),
            verticalScroll_relief=False,
            horizontalScroll_relief=False,
            horizontalScroll_incButton_relief=False,
            horizontalScroll_decButton_relief=False,
            horizontalScroll_thumb_relief=False,
            parent=self._node,
            pos=(0, 1, -self._height))
        self._content_node = self._content_frame.getCanvas().attach_new_node(
            "BufferComponents")
        self._content_node.set_scale(1, 1, -1)
        self._content_node.set_z(self._scroll_height)

        self._chb_show_images = BetterLabeledCheckbox(
            parent=self._node, x=20, y=60, chb_callback=self._set_show_images,
            chb_checked=False, text="Display image resources",
            text_color=Vec3(0.5), expand_width=200)

    def _set_show_images(self, arg):
        self._display_images = arg
        self._perform_update()

    def _remove_components(self):
        """ Removes all components of the buffer viewer """
        self._content_node.node().remove_all_children()
        self._tex_preview.hide()

    def _perform_update(self):
        """ Collects all entries, extracts their images and re-renders the
        window """

        # Collect texture stages
        self._stages = []
        for entry in self._REGISTERED_ENTRIES:
            if isinstance(entry, Texture):
                self._stages.append(entry)
            # Cant use isinstance or we get circular references
            elif entry.__class__.__name__ == "RenderTarget":
                for target in entry.get_all_targets():
                    self._stages.append(entry[target])
            # Cant use isinstance or we get circular references
            elif entry.__class__.__name__ == "Image":
                if self._display_images:
                    self._stages.append(entry.get_texture())
            else:
                self.warn("Unrecognized instance!", entry.__class__)

        self._render_stages()

    def _on_texture_hovered(self, hover_frame, evt=None):
        """ Internal method when a texture is hovered """
        hover_frame["frameColor"] = (0, 0, 0, 0.1)

    def _on_texture_blurred(self, hover_frame, evt=None):
        """ Internal method when a texture is blurred """
        hover_frame["frameColor"] = (0, 0, 0, 0)

    def _on_texture_clicked(self, tex_handle, evt=None):
        """ Internal method when a texture is blurred """
        self._tex_preview.present(tex_handle)

    def _render_stages(self):
        """ Renders the stages to the window """

        self._remove_components()
        entries_per_row = 6
        aspect = Globals.base.win.get_y_size() /\
            float(Globals.base.win.get_x_size())
        entry_width = 235
        entry_height = (entry_width - 20) * aspect + 55

        # Store already processed images
        processed = set()
        index = -1
        # Iterate over all stages
        for stage_tex in self._stages:
            if stage_tex in processed:
                continue
            processed.add(stage_tex)
            index += 1
            stage_name = stage_tex.get_name()

            xoffs = index % entries_per_row
            yoffs = index // entries_per_row
            node = self._content_node.attach_new_node("Preview")
            node.set_sz(-1)
            node.set_pos(10 + xoffs * (entry_width - 14), 1, yoffs * (entry_height-14))

            if stage_name.startswith("Image"):
                r, g, b = 0.4, 0.4, 0.4
            else:
                r, g, b = rgb_from_string(''.join(stage_name.split("-")[:-1]))

            DirectFrame(
                parent=node, frameSize=(7, entry_width - 17, -7, -entry_height + 17),
                frameColor=(r, g, b, 1.0), pos=(0, 0, 0))

            frame_hover = DirectFrame(
                parent=node, frameSize=(0, entry_width - 10, 0, -entry_height + 10),
                frameColor=(0, 0, 0, 0), pos=(0, 0, 0), state=DGG.NORMAL)
            frame_hover.bind(
                DGG.ENTER, partial(self._on_texture_hovered, frame_hover))
            frame_hover.bind(
                DGG.EXIT, partial(self._on_texture_blurred, frame_hover))
            frame_hover.bind(
                DGG.B1PRESS, partial(self._on_texture_clicked, stage_tex))

            BetterOnscreenText(text=stage_name, x=15, y=29, parent=node,
                               size=15, color=Vec3(0.2))

            # Scale image so it always fits
            w, h = stage_tex.get_x_size(), stage_tex.get_y_size()
            scale_x = float(entry_width - 30) / max(1, w)
            scale_y = float(entry_height - 60) / max(1, h)
            scale_factor = min(scale_x, scale_y)

            if stage_tex.get_texture_type() == Texture.TT_buffer_texture:
                scale_factor = 1
                w = entry_width - 30
                h = entry_height - 60

            preview = BetterOnscreenImage(
                image=stage_tex, w=scale_factor * w, h=scale_factor * h,
                any_filter=False, parent=node, x=10, y=40, transparent=False)

            preview.set_shader_input("mipmap", 0)
            preview.set_shader_input("slice", 0)

            preview_shader = DisplayShaderBuilder.build(stage_tex, scale_factor*w, scale_factor*h)
            preview.set_shader(preview_shader)

