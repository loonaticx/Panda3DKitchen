import json

from direct.gui.DirectGui import DGG
from panda3d.core import Filename, Texture

from classes.file.GetDirectory import get_resource_and_filename
from classes.gui.DiscardCanvasButtons import DiscardCanvasButtons
from classes.menus.CanvasMenu import CanvasMenu
from classes.menus.LibraryGui import LibraryGui
from classes.settings import Globals as G

BUTTON_MOVE_TASK = 'button_move'


class LibraryMenu(CanvasMenu, LibraryGui):

    def __init__(self, preview_menu):
        LibraryGui.__init__(self)
        CanvasMenu.__init__(self, preview_menu, self.library_window,
                            self.library_scroll, 'library')
        self.scene_menu = None
        self.scene_window = None
        self.item_name = None
        self.item_location = None
        self.resources = G.RESOURCES
        self.mode = None
        self.class_mode = None
        self.button_copy = None
        self.last_mouse_x = None
        self.last_mouse_y = None
        self.swap_menu = False

    def generate(self):
        self.discard_frame = DiscardCanvasButtons('library',
                                                  self.preview_menu, self,
                                                  self.library_scroll,
                                                  self.library_trash,
                                                  self.library_confirm,
                                                  self.library_folder,
                                                  json=True)
        self.bind_gui()

    def bind_gui(self):
        self.library_folder['command'] = self.choose_file
        self.swap_button['command'] = self.swap_menus

    def swap_menus(self):
        self.swap_menu = not self.swap_menu
        if self.swap_menu:
            self.swap_button.wrt_reparent_to(self.scene_menu.scene_frame)
            self.scene_menu.scene_frame.show()
            self.library_window.hide()
        else:
            self.swap_button.wrt_reparent_to(self.library_window)
            self.scene_menu.scene_frame.hide()
            self.library_window.show()

    def choose_file(self, item_name=None, item_directory=None, search=True,
                    _camera=True):
        self.mode = self.preview_menu.get_mode()
        self.class_mode = self.preview_menu.get_mode_class()

        # Get a file if the mode is not Texture and searching is desired.
        if search and self.mode != 'Texture':
            item_name, item_directory = get_resource_and_filename(
                title=f"Select {self.mode}", initialdir=self.resources)
            if not item_name:
                return

        # default to last used directory in future searches
        self.resources = ""
        if search:
            self.check_for_textures()
            self.check_for_anims()
        base.node_mover.set_click(True)
        self.class_mode.cleanup_entity()

        # try to load the file. return an error if the file cannot be found.
        try:
            self.class_mode.load_entity(item_directory)
        except OSError:
            self.preview_menu.hide_special_buttons()
            return

        self.item_name = item_name
        self.item_location = item_directory

        # Depending the conditions, show the camera, cancel, and/or rng button.
        if self.mode != 'Texture':
            self.preview_menu.hide_mini_window()
            self.preview_menu.mini_window = False
            self.preview_menu.show_preview_buttons(True)
        elif not _camera:
            self.preview_menu.show_preview_buttons(False)
        elif self.mode == 'Texture':
            self.handle_image_data()

    def check_for_textures(self):
        if self.mode == 'Texture':
            texture_names, texture_dirs = get_resource_and_filename(
                title='Select Animations', initialdir=self.resources,
                multiple=True)
            self.class_mode.set_textures(texture_names, texture_dirs)

    def check_for_anims(self):
        if self.mode == 'Actor':
            anim_names, anim_dirs = get_resource_and_filename(
                title='Select Animations', initialdir=self.resources,
                multiple=True)
            self.class_mode.set_anims(anim_names, anim_dirs)
            self.preview_menu.show_dice()

    def handle_image_data(self):
        # save the item to the library database of the specifed mode
        self.class_mode.save_item(self.item_name, self.item_location)
        # capture an image of the model and save it
        if self.mode != 'Texture':
            self.preview_menu.flash_screen()  # play a camera flash animation
            self.capture_and_save_image()
        self.reload()
        self.preview_menu.hide_special_buttons()

    def capture_and_save_image(self):
        # make a temporary scene off screen to get a picture and save it.
        buffer = base.win.make_texture_buffer("buffer", 128, 128, Texture(),
                                              to_ram=True)
        buffer.set_sort(-100)
        camera = base.make_camera(buffer)
        camera.node().get_lens().set_fov(G.PREVIEW_FOV)
        camera.reparent_to(base.preview_render)
        path = f"{G.RESOURCES}{G.EDITOR}{self.mode}/{self.item_name}.png"
        # reassign the destination to the entire directory location
        file_name = Filename.from_os_specific(base.root_folder + path)

        base.graphicsEngine.render_frame()
        buffer.save_screenshot(file_name)

        # cleanup
        base.graphicsEngine.remove_window(buffer)
        camera.remove_node()

    def reload(self):
        mode = self.preview_menu.get_mode()
        mode_class = self.preview_menu.get_mode_class()
        library_path = f"{G.DATABASE_DIRECTORY}{mode}Library.json"
        library_dict = json.loads(open(library_path).read())
        for button in mode_class.library_buttons:
            button.destroy()

        self.load_picture_list(library_dict,
                               button_increase=True,
                               button_copy=self.make_button_copy,
                               add_to_scene=self.add_item_to_scene,
                               color=(.9, .9, .7, 1))

    def make_button_copy(self, button, mouse_data):
        if self.discard_frame.trash_mode:  # Don't move during trash mode.
            return
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        # generate a copy and set the position.
        self.button_copy = button['geom'].copy_to(button)
        self.button_copy.wrt_reparent_to(aspect2d)
        self.button_copy.set_alpha_scale(.75)
        self.button_copy.set_name(button.get_name())

        taskMgr.add(self.update_button_copy_pos, BUTTON_MOVE_TASK)

    def update_button_copy_pos(self, task):
        if base.mouseWatcherNode.has_mouse() and self.button_copy:
            mouse_pos = base.mouseWatcherNode.getMouse()
            aspect = base.getAspectRatio()
            self.button_copy.set_pos(mouse_pos.x * aspect, 0, mouse_pos.y)
            return task.again
        else:
            return task.done

    def add_item_to_scene(self, mouse_data):
        # The scene that the item can be added to is either the
        # preview scene or the actual scene
        if self.discard_frame.trash_mode:  # Don't add during trash mode.
            return
        mode = self.preview_menu.get_mode()
        class_mode = self.preview_menu.get_mode_class()

        if self.scene_window.within:
            if (base.top_window != 'preview_window'
                    or not self.preview_menu.within):
                self.scene_menu.add_item_to_xml(self.button_copy.get_name())

        if self.preview_menu.within:
                item_name = self.button_copy.get_name()
                json_path = f"{G.DATABASE_DIRECTORY}{mode}Library.json"
                json_data = json.loads(open(json_path).read())
                item_directory = self.check_for_actor(mode, json_data,
                                                      item_name, class_mode)
                self.choose_file(item_name, item_directory, search=False,
                                 _camera=False)

        self.button_copy.remove_node()

    def check_for_actor(self, mode, json_data, item_name, class_mode):
        item_directory = json_data[item_name]
        if mode == 'Actor':
            data = json_data[item_name]
            item_directory = data[0]
            class_mode.anim_list = data[1]
            self.preview_menu.show_dice()

        return item_directory

    def set_scene_menu(self, menu):
        self.scene_menu = menu

    def set_scene_window(self, window):
        self.scene_window = window