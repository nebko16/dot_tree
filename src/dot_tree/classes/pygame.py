from __future__ import annotations
import os
import re
import pygame
import mimetypes
from dot_tree.classes.assets import DotTree, DotTreeBranch, AppData, logger

screen: pygame.Surface = None


def _pygame_init():
    if not pygame.get_init():
        raise Exception("Pygame must be initialized before using this method")


def _pygame_display_init():
    _pygame_init()
    if not pygame.display.get_init():
        raise Exception("Pygame display must be initialized before using this method")


def _pygame_mixer_init():
    _pygame_init()
    if not pygame.mixer.get_init():
        raise Exception("Pygame mixer must be initialized before using this method")


def _pygame_font_init():
    _pygame_init()
    if not pygame.font.get_init():
        raise Exception("Pygame font must be initialized before using this method")


class GameDotTreeBranch(DotTreeBranch):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cached_asset: any = None

    def load(self,
             alpha: bool = True,
             scaled_width: int = None,
             scaled_height: int = None,
             scale_percent: float = None,
             volume: float = 0.5,
             font_size: int = 24,
             mode: str = 'auto'):
        """
        the behavior of this override method is different from the base class

        when called on a file node, this version loads the asset or retrieves
        it from cache if already cached, then returns it, like the base class

        but if you call this on a directory node, it does the same thing, but for
        all files in the directory, and returns a python list of the loaded assets

        this only loads the assets in the immediate directory, and is not recursive

        this is useful when loading sprite group assets or parallax backgrounds, etc
        """
        if self.is_file:
            return self._load(alpha,
                              scaled_width,
                              scaled_height,
                              scale_percent,
                              volume,
                              font_size,
                              mode=mode)
        else:
            files = []
            for file in self.files.values():
                files.append(file.load(alpha,
                                       scaled_width,
                                       scaled_height,
                                       scale_percent,
                                       volume,
                                       font_size,
                                       mode=mode))
            return files

    def _load(self,
              alpha: bool = True,
              scaled_width: int = None,
              scaled_height: int = None,
              scale_percent: float = None,
              volume: float = 0.5,
              font_size: int = 24,
              mode: str = 'auto'):

        if self._cached_asset is None:
            ext = os.path.splitext(self.path)[1].lower()
            file_type = GameDotTree.file_extensions.get(ext)
            mime_type, _ = mimetypes.guess_type(self.path)

            if mode != 'auto':
                with open(self.path, mode) as f:
                    self._cached_asset = f.read()

            elif file_type == 'image' or mime_type and mime_type.startswith('image'):
                _pygame_display_init()
                self._cached_asset = pygame.image.load(self.path)
                if alpha:
                    self._cached_asset = self._cached_asset.convert_alpha()
                else:
                    self._cached_asset = self._cached_asset.convert()

                if scaled_width or scaled_height or scale_percent:
                    original_width, original_height = self._cached_asset.get_size()
                    new_width, new_height = original_width, original_height

                    if scale_percent:
                        if scale_percent > 5:
                            logger.warning("scale percent is meant to be a float "
                                           "between 0 and 1. values above 25 are "
                                           "assumed to be 0-100 scale and converted "
                                           "automatically")
                        divisor = 100 if scale_percent > 25 else 1
                        if divisor == 0:
                            divisor = 0.001
                        new_width = int(original_width * scale_percent / divisor)
                        new_height = int(original_height * scale_percent / divisor)
                    elif scaled_width:
                        new_width = scaled_width
                        new_height = int(original_height * (scaled_width / original_width))
                    elif scaled_height:
                        new_height = scaled_height
                        new_width = int(original_width * (scaled_height / original_height))

                    self._cached_asset = pygame.transform.smoothscale(self._cached_asset, (new_width, new_height))

            elif file_type == 'sound' or mime_type and mime_type.startswith('audio'):
                _pygame_mixer_init()
                self._cached_asset = pygame.mixer.Sound(self.path)
                self._cached_asset.set_volume(volume)

            elif file_type == 'font' or mime_type and mime_type.startswith('font'):
                _pygame_font_init()
                self._cached_asset = pygame.font.Font(self.path, font_size)

            elif file_type in DotTree.text_extensions or mime_type and mime_type.startswith('text'):
                with open(self.path, 'r') as f:
                    self._cached_asset = f.read()
            else:
                with open(self.path, 'rb') as f:
                    self._cached_asset = f.read()

        return self._cached_asset

    def info(self, image_node: GameDotTreeBranch = None, to_stdout: bool = True):
        surface: pygame.Surface | None = None
        if isinstance(image_node, GameDotTreeBranch):
            surface = image_node.load()
        if image_node is None and self._cached_asset:
            surface = self._cached_asset
        if isinstance(surface, pygame.Surface):
            if isinstance(image_node, GameDotTreeBranch):
                size: str = image_node.size(to_stdout=False)
            else:
                size: str = self.size(to_stdout=False)
            stats = {
                'resolution': (surface.width, surface.height),
                'width': surface.width,
                'height': surface.height,
                'pixels': surface.width * surface.height,
                'aspect': f"{round(surface.width/surface.height, 2)}:1",
                'color_bit_depth': surface.get_bitsize(),
                'has_alpha': bool(surface.get_flags() & pygame.SRCALPHA),
                'color_key': surface.get_colorkey(),
                'size': size
            }
            if to_stdout:
                output = f"\n\n\n\n Resolution: {stats['width']} x {stats['height']}\n"
                output += f"     Aspect: {stats['aspect']}\n"
                output += f"     Pixels: {stats['pixels']:,d}\n"
                output += f"       Size: {stats['size']}\n"
                output += f"Color Depth: {stats['color_bit_depth']}-bit\n"
                output += f"  Has Alpha: {stats['has_alpha']}\n"
                output += f"  Color Key: {stats['color_key']}\n\n"
                print(output)
            return stats
        else:
            print(type(surface))
            raise TypeError(
                "at the moment, info() method only supports pygame.Surface objects "
                "either by argument, or local cache if it's already loaded.")
    stats = info
    details = info

    def build_tree(self, path):
        ignore_pattern = re.compile('|'.join(GameDotTree.ignored_files))
        for node in os.listdir(path):
            if ignore_pattern.search(node):
                continue
            child_path = os.path.join(path, node)
            py_name = GameDotTree.normalize_name(node)
            child_dot_path = f"{self.dot_path}.{py_name}"

            if os.path.isdir(child_path):
                subdir = GameDotTreeBranch(py_name.lower(),
                                           node,
                                           child_path,
                                           child_dot_path,
                                           parent=self,
                                           trunk=self.trunk)
                self.children[py_name.lower()] = subdir
                subdir.build_tree(child_path)
            else:
                if '.' in py_name:
                    base_name = py_name.split('.')[0]
                    extension = py_name.split('.')[1]
                else:
                    base_name = py_name
                    extension = None
                if base_name[0:1].isnumeric():
                    base_name = f"_{base_name}"
                file = GameDotTreeBranch(base_name.lower(),
                                         node,
                                         child_path,
                                         child_dot_path,
                                         parent=self,
                                         trunk=self.trunk,
                                         extension=extension,
                                         is_file=True)
                self.files_base_name[base_name.lower()] = file
                self.files[py_name.lower()] = file


class GameDotTree(DotTree):
    r"""
    Extension of Dot Tree asset manager for PyGame.

    Load()/Preload() automatically loads assets into PyGame objects.

    - Images get loaded as pygame.surface.Surface
    - Sounds get loaded as pygame.mixer.Sound
    - Fonts get loaded as pygame.font.Font
    """

    file_extensions = {
        '.png': 'image',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.gif': 'image',
        '.bmp': 'image',
        '.pcx': 'image',
        '.tga': 'image',
        '.tif': 'image',
        '.tiff': 'image',
        '.lbm': 'image',
        '.pbm': 'image',
        '.pgm': 'image',
        '.ppm': 'image',
        '.xpm': 'image',
        '.wav': 'sound',
        '.ogg': 'sound',
        '.mp3': 'sound',
        '.ttf': 'font',
        '.otf': 'font'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cached_asset: any = None
        self.dot_path = '<GameDotTree>'

    def load(self,
             alpha: bool = True,
             scaled_width: int = None,
             scaled_height: int = None,
             scale_percent: float = None,
             volume: float = 0.5,
             font_size: int = 24,
             mode: str = 'auto'):
        """
        the behavior of this override method is different from the base class

        when called on a file node, this version loads the asset or retrieves
        it from cache if already cached, then returns it, like the base class

        but if you call this on a directory node, it does the same thing, but for
        all files in the directory, and returns a python list of the loaded assets

        this only loads the assets in the immediate directory, and is not recursive

        this is useful when loading sprite group assets or parallax backgrounds, etc
        """
        files = []
        for file in self.files.values():
            files.append(file.load(alpha, scaled_width, scaled_height, scale_percent, volume, font_size, mode=mode))
        return files

    def build_tree(self, path):
        ignore_pattern = re.compile('|'.join(self.ignored_files))
        for node in os.listdir(path):
            if ignore_pattern.search(node):
                continue
            child_path = os.path.join(path, node)
            child_dot_path = f"{self.dot_path}.{self.normalize_name(node)}"

            py_name = self.normalize_name(node)
            if py_name != node:
                self.name_mappings.update({node: py_name})
            py_name = py_name.lower()
            if os.path.isdir(child_path):
                subdir = GameDotTreeBranch(py_name,
                                           node,
                                           child_path,
                                           child_dot_path,
                                           parent=self,
                                           trunk=self)
                self.children[py_name] = subdir
                subdir.build_tree(child_path)
            else:
                if '.' in py_name:
                    base_name = py_name.split('.')[0].strip().lower()
                    extension = py_name.split('.')[1].strip().lower()
                else:
                    base_name = py_name.strip().lower()
                    extension = None
                if base_name[0:1].isnumeric():
                    base_name = f"_{base_name}"
                file = GameDotTreeBranch(base_name,
                                         node,
                                         child_path,
                                         child_dot_path,
                                         parent=self,
                                         trunk=self,
                                         extension=extension,
                                         is_file=True)
                self.files_base_name[base_name] = file
                self.files[py_name] = file

    @staticmethod
    def info(image_node: GameDotTreeBranch, to_stdout: bool = True):
        surface = image_node.load()
        if isinstance(surface, pygame.Surface):
            stats = {
                'resolution': (surface.width, surface.height),
                'width': surface.width,
                'height': surface.height,
                'pixels': surface.width * surface.height,
                'aspect': f"{round(surface.width/surface.height, 2)}:1",
                'color_bit_depth': surface.get_bitsize(),
                'has_alpha': bool(surface.get_flags() & pygame.SRCALPHA),
                'color_key': surface.get_colorkey(),
                'size': image_node.size(to_stdout=False)
            }
            if to_stdout:
                output = f"\n\n\n\n Resolution: {stats['width']} x {stats['height']}\n"
                output += f"     Aspect: {stats['aspect']}\n"
                output += f"     Pixels: {stats['pixels']:,d}\n"
                output += f"       Size: {stats['size']}\n"
                output += f"Color Depth: {stats['color_bit_depth']}-bit\n"
                output += f"  Has Alpha: {stats['has_alpha']}\n"
                output += f"  Color Key: {stats['color_key']}\n\n"
                print(output)
            return stats
        else:
            print(type(surface))
            raise TypeError(
                "at the moment, info() method only supports pygame.Surface objects "
                "either by argument")
    stats = info
    details = info



class GameData(AppData):
    r"""
    Extension of the AppData class, which is a wrapper for the `appdirs` module.

    This extension just adds screenshot folder support to make it easier to
    create and manage a screenshots folder stored with other app data.

    It creates a file per user per app to store json data related to screenshots,
    but in most cases, you'd likely just use this to get the
    GameData.screenshots_path value.  It will create the directories if they don't
    exist, and you can grab the full path from the `screenshots_path` attribute.

    """
    def __init__(self,
                 app_name: str,
                 app_user: str | None = None,
                 app_author: str | None = None,
                 app_version: str | None = '1.0'):

        super().__init__(app_name, app_user, app_author, app_version)

        self.screenshots_path: str | None = None
        self.screenshots: str | None = None
        self.screenshots, self.screenshots_path = self._build_('screenshots')

    def load_screenshots(self) -> dict:
        r"""
        this loads a json file in the screenshots folder for this app/user,
        so you'd only use this if you needed to keep metadata for your
        screenshots, otherwise just use the screenshots_path attribute and
        access the screenshots directly
        """
        return self._load_(self.screenshots)

    def save_screenshots(self, data: dict):
        r"""
        this saves a json file in the screenshots folder for this app/user,
        so you'd only use this if you needed to keep metadata for your
        screenshots, otherwise just use the screenshots_path attribute and
        access the screenshots directly
        """
        self._save_(data, self.screenshots)


