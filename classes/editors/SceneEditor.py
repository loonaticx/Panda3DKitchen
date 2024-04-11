"""
A collection of different classes. Mashes them together into an editor.
"""
from direct.showbase.DirectObject import DirectObject

from classes.camera.RotationalCamera import RotationalCamera
from classes.camera.FovScrollWheel import FovScrollWheel
from .NodeMover import NodeMover
from .NodeSelector import NodeSelector


class SceneEditor(DirectObject):

    def __init__(self, cameras=None, mouse_watcher=None,
                 display_region=None, _render=False,
                 rot_cam_disable=True, fov=None):
        DirectObject.__init__(self)
        self.cameras = []
        self.mouse_watcher = mouse_watcher
        # Fall back on base mouseWatcherNode if no mw is passed in.
        if not self.mouse_watcher:
            self.mouse_watcher = base.mouseWatcherNode
        self.display_region = display_region
        self.render = _render
        # Fall back on base render if no other render is specified.
        if not _render:
            self.render = render
        self.rot_cam_disable = rot_cam_disable
        self.fov = fov
        self.node_selectors = None
        self.orb_cam = None
        self.hide_gui = False

        if cameras:  # Get the last camera from the list
            self.generate_features(cameras[-1])
        else:  # Default to og camera.
            self.generate_features(camera)

    def generate_features(self, camera):
        base.rot_cam = RotationalCamera(camera, self.rot_cam_disable)
        base.fov_wheel = FovScrollWheel(self.fov, camera, self.mouse_watcher)
        base.node_mover = NodeMover(camera, camera)
        base.node_selector = NodeSelector(camera, self.render,
                                          self.mouse_watcher, base.node_mover)

    def cleanup(self):
        classes = [base.node_mover, base.node_selector, base.fov_wheel]
        if self.orb_cam:
            classes.append(self.orb_cam)

        for selector in self.node_selectors:
            selector.cleanup()

        for class_item in classes:
            class_item.cleanup()