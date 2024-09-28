import os
import re
import json
import appdirs
import logging
import keyword
import unicodedata


logger = logging.getLogger(__name__)



class DotTreeBranch(os.PathLike):

    def __init__(self,
                 py_name,
                 os_name,
                 path,
                 parent,
                 is_file=False,
                 extension=None):
        self.parent = parent
        self.py_name = py_name
        self.os_name = os_name
        self.path = path
        self.children = {}
        self.files_base_name = {}
        self.files = {}
        self.is_file = is_file
        self.extension = extension
        self.extension_referenced = False
        self._cached_asset = None

    def __str__(self):
        if not self.extension_referenced and self.is_file:
            raise AttributeError(f"Files must include extension.")
        self.extension_referenced = False
        return str(self.path)

    def __fspath__(self):
        return self.__str__()

    def open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        return open(self.__fspath__(), mode, buffering, encoding, errors, newline)

    def get_size(self, units='auto', return_only_value=False, child=False, to_stdout=True):

        if not units:
            raise Exception("\n\n\n    Units must be: auto, B, KB, MB, GB, or TB.\n")

        size: float = 0

        if self.is_file:
            size = os.path.getsize(self.path)
        else:
            for file in self.files.values():
                size += file.get_size(child=True)

            for subdir in self.children.values():
                size += subdir.get_size(child=True)

        if child:
            return size

        the_size = DotTree.filesizes(size, units, return_only_value)
        if to_stdout:
            print(the_size)
        return the_size
    size = get_size

    def __getattr__(self, raw_name):
        name = raw_name.strip().lower()
        if self.is_file and name == self.extension:
            self.extension_referenced = True
            return self

        elif self.is_file and name != self.extension:
            real_name = f"{self.py_name}.{name}"
            if real_name in self.parent.files:
                sibling = self.parent.files[real_name]
                sibling.extension_referenced = True
                return sibling

        if name in self.children:
            return self.children[name]

        if not self.is_file and name in self.files_base_name:
            return self.files_base_name.get(name)

        base_path = os.path.dirname(self.path)
        base_filename = self.os_name
        if '.' in base_filename:
            base_filename = self.os_name.split('.')[0]
        filepath = os.path.join(base_path, base_filename)
        needle = f"{filepath}.{raw_name}"
        error_msg = f"\n\nFile `{needle}` not found.\n\nFiles in this directory:\n"

        if self.parent.files:
            for sibling in self.parent.files.values():
                error_msg += f"  {sibling.os_name}\n"

        raise AttributeError(f"{error_msg}\n\n")

    def __getitem__(self, key):
        if key in self.children:
            return self.children[key]
        elif key in self.files:
            return self.files[key]
        else:
            raise KeyError(f"'{key}' not found in this DotTreeBranch")

    def get(self, key, default=None):
        if key in self.children:
            return self.children[key]
        elif key in self.files:
            return self.files[key]
        return default

    def preload(self):
        for subdir in self.children.values():
            subdir.preload()
        for asset in self.files.values():
            asset.load()
        return self
    precache = preload

    def build_tree(self, path):
        ignore_pattern = re.compile('|'.join(DotTree.ignored_files))
        for node in os.listdir(path):
            if ignore_pattern.search(node):
                continue
            child_path = os.path.join(path, node)
            py_name = DotTree.normalize_name(node)
            py_name = py_name.lower()
            if os.path.isdir(child_path):
                subdir = DotTreeBranch(py_name, node, child_path, parent=self)
                self.children[py_name] = subdir
                subdir.build_tree(child_path)
            else:
                if '.' in py_name:
                    base_name = py_name.split('.')[0].strip().lower()
                else:
                    base_name = py_name.strip().lower()
                if '.' in py_name:
                    extension = py_name.split('.')[1].strip().lower()
                else:
                    extension = None
                file = DotTreeBranch(base_name,
                                     node,
                                     child_path,
                                     parent=self,
                                     extension=extension,
                                     is_file=True)
                self.files_base_name[base_name] = file
                self.files[py_name] = file

    def load(self, mode='auto', decode: str = None):
        if not self.is_file:
            raise AttributeError("\n\n  load() is for file nodes.\n\n  "
                                 f"This node is a directory: {self.path}\n\n")
        if self._cached_asset is None:
            ext = os.path.splitext(self.path)[1].lower().replace('.', '')
            if ext.lower() in DotTree.text_extensions or mode == 'r':
                try:
                    with open(self.path, 'r') as f:
                        self._cached_asset = f.read()
                except UnicodeDecodeError:
                    with open(self.path, 'rb') as f:
                        self._cached_asset = f.read()
            else:
                with open(self.path, 'rb') as f:
                    self._cached_asset = f.read()
        if decode:
            self._cached_asset = self._cached_asset.decode(decode)
        return self._cached_asset

    def unload(self):
        if self.is_file:
            self._cached_asset = None
            return
        for file in self.files.values():
            file.unload()
        for child in self.children.values():
            child.unload()

    def show_tree(self, node=None):
        if not node:
            node = self
        if self.is_file:
            logger.warning(f"\n\n  tree() is for directory nodes.\n\n  This node is a file: {self.os_name}\n\n")
            return ''
        return self.parent.show_tree(node=node)
    tree = show_tree

    def list(self):
        dirs = []
        for child in self.children.values():
            dirs.append(f"{child.os_name}/")
        dirs.sort()
        files = []
        for child in self.files.values():
            files.append(f"{child.os_name}")
        files.sort()
        dirs.extend(files)
        return dirs
    ls = list


class DotTree:
    ignored_files = [
        r'\.DS_Store$',
        r'\.py[cod]$',
        r'__pycache__',
        r'\.git',
        r'\.svn',
        r'\.hg',
        r'__pycache__',
        r'\.vscode',
        r'\.idea',
        r'\.env',
        r'Thumbs\.db$',
        r'\.bak$',
        r'~$',
    ]

    text_extensions = {
        "ada",
        "adb",
        "ads",
        "asc",
        "asm",
        "bash",
        "bat",
        "c",
        "cfg",
        "clj",
        "cljs",
        "cmd",
        "coffee",
        "conf",
        "cpp",
        "cs",
        "css",
        "csv",
        "d",
        "dart",
        "diff",
        "docx",
        "elm",
        "erl",
        "ex",
        "exs",
        "f",
        "f90",
        "f95",
        "for",
        "fs",
        "fsx",
        "go",
        "groovy",
        "gsh",
        "gvy",
        "gy",
        "h",
        "hpp",
        "hrl",
        "hs",
        "htm",
        "html",
        "ini",
        "java",
        "jl",
        "js",
        "json",
        "kt",
        "lhs",
        "lisp",
        "litcoffee",
        "log",
        "lsp",
        "lua",
        "m",
        "markdown",
        "md",
        "ml",
        "mli",
        "mm",
        "nim",
        "odg",
        "odp",
        "ods",
        "odt",
        "otg",
        "otp",
        "ots",
        "ott",
        "pas",
        "patch",
        "php",
        "phps",
        "phtml",
        "pl",
        "pptx",
        "properties",
        "ps1",
        "py",
        "r",
        "rb",
        "rs",
        "rst",
        "rtf",
        "s",
        "scala",
        "scm",
        "sh",
        "sql",
        "srt",
        "ss",
        "swift",
        "tcl",
        "tex",
        "toml",
        "ts",
        "tsv",
        "txt",
        "v",
        "vb",
        "vbs",
        "vhd",
        "vtt",
        "xhtml",
        "xlsx",
        "xml",
        "yaml",
        "yml"
    }

    def __init__(self, assets_path: str):
        assets_path = os.path.abspath(assets_path)
        if not os.path.exists(assets_path):
            raise FileNotFoundError(f"Directory {assets_path} not found.")
        if not os.path.isdir(assets_path):
            raise FileNotFoundError(f"{assets_path} is not a directory.")
        self.path = assets_path
        self.os_name = os.path.basename(os.path.dirname(assets_path))
        self.children = {}
        self.is_file = False
        self.name_mappings = {}
        self.files_base_name = {}
        self.files = {}
        self.build_tree(self.path)

    def __str__(self):
        return self.path

    def __getattr__(self, raw_name):
        name = raw_name.strip().lower()
        if name in self.children:
            return self.children[name]
        if name in self.files:
            return self.files[name]
        if name in self.files_base_name:
            return self.files_base_name[name]
        raise AttributeError(f"file or folder `{raw_name}` not found")

    def __getitem__(self, raw_key):
        key = raw_key.strip().lower()
        if key in self.children:
            return self.children[key]
        if key in self.files:
            return self.files[key]
        if key in self.files_base_name:
            return self.files_base_name[key]
        raise KeyError(f"file or folder `{raw_key}` not found")

    def get(self, key, default=None):
        if key in self.children:
            return self.children[key]
        elif key in self.files:
            return self.files[key]
        return default

    def build_tree(self, path):
        ignore_pattern = re.compile('|'.join(self.ignored_files))
        for node in os.listdir(path):
            if ignore_pattern.search(node):
                continue
            child_path = os.path.join(path, node)

            py_name = self.normalize_name(node)
            if py_name != node:
                self.name_mappings.update({node: py_name})
            py_name = py_name.lower()
            if os.path.isdir(child_path):
                subdir = DotTreeBranch(py_name,
                                   node,
                                   child_path,
                                   parent=self)
                self.children[py_name] = subdir
                subdir.build_tree(child_path)
            else:
                base_name = py_name.split('.')[0].strip().lower()
                if base_name[0:1].isnumeric():
                    base_name = f"_{base_name}"
                if '.' in py_name:
                    extension = py_name.split('.')[1].strip().lower()
                else:
                    extension = None
                file = DotTreeBranch(base_name,
                                     node,
                                     child_path,
                                     parent=self,
                                     extension=extension,
                                     is_file=True)
                self.files_base_name[base_name] = file
                self.files[py_name] = file

    def preload(self):
        for subdir in self.children.values():
            subdir.preload()
        for asset in self.files.values():
            asset.load()
        return self
    precache = preload

    def unload(self):
        for file in self.files.values():
            file.unload()
        for child in self.children.values():
            child.unload()

    def show_tree(self, node=None, to_stdout=True):
        if not node:
            node = self

        if node.is_file:
            logger.warning(f"\n\n  tree() is for directory nodes.\n\n  This node is a file: {node.os_name}\n\n")
            return

        def _show_tree(node, level=0):
            tree = []
            files = {}
            file_sizes = {}
            for child in node.children.values():
                subdir_row = f"{child.get_size(to_stdout=False).rjust(10)}   {'   ' * level}{child.os_name}/"
                if subdir_row:
                    tree.append(subdir_row)
                tree.extend(_show_tree(child, level + 1))

            for child in node.files.values():
                if child.extension not in files:
                    files[child.extension] = 0
                    file_sizes[child.extension] = 0
                files[child.extension] += 1
                file_sizes[child.extension] += child.get_size(units='B', return_only_value=True, to_stdout=False)

            if files:
                keys = list(files.keys())
                keys.sort()
                for key in keys:
                    ext = key
                    count = files[key]
                    size = DotTree.filesizes(file_sizes[key]).rjust(10)
                    file_row = f"{size}   {'   ' * level} *.{ext} ({count})"
                    tree.append(file_row)
            return tree
        tree = _show_tree(node)
        the_tree = '\n'.join(tree)
        if to_stdout:
            print(the_tree)
        return the_tree
    tree = show_tree

    def get_size(self, units='auto', return_only_value=False, child=False, to_stdout=True):

        if not units:
            raise Exception("\n\n\n    Units must be: auto, B, KB, MB, GB, or TB.\n")

        size: float = 0
        if self.is_file:
            size = os.path.getsize(self.path)
        else:
            for file in self.files.values():
                size += file.get_size(child=True)

            for subdir in self.children.values():
                size += subdir.get_size(child=True)

        if child:
            return size

        the_size = self.filesizes(size, units, return_only_value)
        if to_stdout:
            print(the_size)
        return the_size
    size = get_size

    @staticmethod
    def filesizes(size_bytes: float,
                  units: str = 'auto',
                  return_only_value: bool = False,
                  places: int = 2):

        if not units:
            raise Exception("\n\n\n    Units must be: auto, B, KB, MB, GB, or TB.\n")

        if (units == 'auto' and size_bytes > 1024 ** 4) or units == 'TB':
            size_bytes = size_bytes / 1024 / 1024 / 1024 / 1024
            units = 'TB'

        elif (units == 'auto' and size_bytes > 1024 ** 3) or units == 'GB':
            size_bytes = size_bytes / 1024 / 1024 / 1024
            units = 'GB'

        elif (units == 'auto' and size_bytes > 1024 ** 2) or units == 'MB':
            size_bytes = size_bytes / 1024 / 1024
            units = 'MB'

        elif (units == 'auto' and size_bytes > 1024) or units == 'KB':
            size_bytes = size_bytes / 1024
            units = 'KB'

        size_bytes = round(size_bytes, places)
        if return_only_value:
            return size_bytes
        if units == 'auto':
            units = 'B'
        return f"{size_bytes} {units}"

    def list(self):
        dirs = []
        for child in self.children.values():
            dirs.append(f"{child.os_name}/")
        dirs.sort()
        files = []
        for child in self.files.values():
            files.append(f"{child.os_name}")
        files.sort()
        dirs.extend(files)
        return dirs
    ls = list

    def show_name_mappings(self):
        print('\n\n')
        for original, normalized in self.name_mappings.items():
            print(f"{original} -> {normalized}")
        print('\n\n')

    @staticmethod
    def normalize_name(original_name):
        if original_name is None:
            return None
        name = unicodedata.normalize('NFC', original_name)
        name = name.replace(' ', '_').replace('-', '_')
        name = ''.join(c for c in name if c.isalnum() or c in ['_', '.'])
        if name and not name[0].isalpha() and name[0] != '_':
            name = '_' + name
        if keyword.iskeyword(name.split('.')[0]):
            name = '_' + name
        if original_name != name:
            logger.debug(f"{original_name} -> {name}")
        return name

    def get_node(self, path: str):
        r"""
        this was created to allow retrieval of a node or branch by a path
        in string format, in order to accommodate the possibility of a static
        text config file.  you can use slashes instead of dot notation, but
        you'll still need to use normalized names like you would when using
        dot_tree directly, so 1_tree.png would need to be _1_tree.png, and
        'big tree.bmp' would need to be 'big_tree.bmp', and so on.

        Example:

          assets = DotTree('../assets')

          path = 'tiles/animated_orc/walking/orc_walking.png'
          node = assets.get_node(path)

          print(node)
          # output: C:\usr\local\repos\dot_tree\src\dot_tree\assets\tiles\animated_orc\Walking\Orc_Walking.png

        """
        path = path.replace('\\', '/')
        if path.endswith('/'):
            path = path[:-1]
        nodes = path.split('/')
        tree = self
        for node in nodes:
            node = DotTree.normalize_name(node).strip().lower()
            tree = tree.get(node)
            if not tree:
                return None
            if tree.is_file:
                tree.extension_referenced = True
                return tree
        return tree


class AppData:
    r"""
    this is just a wrapper for the excellent existing `appdirs` module to simplify the
    usage syntax into simply saving and loading app data to and from a python
    dictionary, so other than the import and the instantiation, you only need a single
    line of code to save or load your app data. the underlying `appdirs` module stores
    the data in the appropriate OS specific locations:

    macOS:
      ~/Library/Application Support/<app_name>

    Linux/Unix:
      ~/.local/share/<app_name>

    Windows XP:
      C:\Documents and Settings\<windows_username>\Application Data\<app_name>

    Windows 7+:
      C:\Users\<windows_username>\AppData\Local\<app_author>\<app_name>

    The ~ for the mac and linux/unix ones is a shortcut for $HOME, or the
    user's home directory. Replacing the ~ with your full home directory
    path would be equivalent.  Since I'm making this wrapper to make it
    easier for beginners, I figured this might be worth mentioning.

    for the simplest usage, you can just use load() and save(), but for more granular
    control of the data for when you want to organize it separately, you can use the
    individual directories created automatically to store specific data separately:

    # load() and save() are just aliases for these
      load_data(), save_data()

    # you can use this if you want to store configuration data separately
      load_config(), save_config()

    # you can use this to load and store cache data separately
      load_cache(), save_cache()

    # you can use this to load and save log data separately
      load_log(), save_log()

    # typically, log data would not be in json, and dumped into a log directory, so
    # you can just access the log_path property and just write log files to the log
    # subdirectory directly, and this module can still at least help you store it
    # per app and user, ensuring the directory exists and such
      app_data = AppData('MyApp', 'MyUser')
      log_path = app_data.log_path

    # there are equivalent path properties for the rest, so you can always just use
    # this to get the directory structure created and an easy way to acces them

    Example of the most basic usage:

        from dot_tree import AppData
        app_data = AppData('MyApp')

        # save app data
        your_app_data = {'high_score': 9001, 'current_level': 3}
        app_data.save(your_app_data)

        # load app data
        your_app_data = app_data.load()
        high_score = your_app_data.get['high_score']

    Example of more granular usage:

        from dot_tree import AppData
        app_data = AppData('MyApp')

        # load config data
        config = app_data.load_config()

        # load game state
        state = app_data.load_state()

        # save config data
        app_data.save_config(config)

        # save game state
        app_data.save_state(state)

    """

    def __init__(self,
                 app_name: str,
                 app_user: str | None = 'user',
                 app_author: str | None = None,
                 app_version: str | None = '1.0'):

        self.app_user = DotTree.normalize_name(app_user)
        self.app_name = DotTree.normalize_name(app_name)

        self.app_author: str = app_author
        if self.app_author:
            self.app_author = DotTree.normalize_name(self.app_author)

        app_version = str(app_version).lower()
        if not app_version.startswith('v'):
            app_version = f"v{app_version}"
        self.app_version: str = app_version
        self.filename = f"{self.app_version}_{self.app_user}.json"

        self.app_data: dict = dict()
        self.base_path: str | None = None

        self.data_path: str | None = None
        self.data: str | None = None

        self.config_path: str | None = None
        self.config: str | None = None

        self.cache_path: str | None = None
        self.cache: str | None = None

        self.state_path: str | None = None
        self.state: str | None = None

        self.log_path: str | None = None
        self.log: str | None = None

        self._init_paths_()

    def _init_paths_(self):
        """ build base path """
        base_path: str = appdirs.user_data_dir(self.app_name, self.app_author, roaming=True)
        if not os.path.exists(base_path):
            base_path: str = appdirs.user_data_dir(self.app_name, self.app_author)
        self.base_path = base_path

        """ data """
        self.data, self.data_path = self._build_('data')

        """ config """
        self.config, self.config_path = self._build_('config')

        """ cache """
        self.cache, self.cache_path = self._build_('cache')

        """ state """
        self.state, self.state_path = self._build_('state')

        """ log """
        self.log, self.log_path = self._build_('log')

    def _build_(self, path_name: str) -> tuple[str, str]:
        r"""
        saves the filename with version pre-pended, so you can
        have version control to avoid problems with changes to
        your app that break compatibility with older saves
        syntax: <version>_<user>.json
        """
        path: str = os.path.join(self.base_path, path_name)
        os.makedirs(path, exist_ok=True)
        filepath = os.path.join(path, self.filename)
        return filepath, path

    def load_data(self) -> dict:
        return self._load_(self.data)

    load: callable = load_data

    def save_data(self, data: dict):
        self._save_(data, self.data)

    save: callable = save_data

    def load_config(self) -> dict:
        return self._load_(self.config)

    def save_config(self, data: dict):
        self._save_(data, self.config)

    def load_cache(self) -> dict:
        return self._load_(self.cache)

    def save_cache(self, data: dict):
        self._save_(data, self.cache)

    def load_state(self) -> dict:
        return self._load_(self.state)

    def save_state(self, data: dict):
        self._save_(data, self.state)

    def load_log(self) -> dict:
        return self._load_(self.log)

    def save_log(self, data: dict):
        self._save_(data, self.log)

    @staticmethod
    def _save_(app_data: dict, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(app_data, f)

    def _load_(self, filepath: str) -> dict:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                app_data: dict = json.load(f)
            return app_data
        else:
            logger.warning(f"\n\n  file for version {self.app_version} not found.\n")
            directory = os.path.dirname(filepath)
            files = [f for f in os.listdir(directory) if f.endswith(f"_{self.app_user}.json")]
            if not files:
                return {}
            latest_file = max(files)
            filepath = os.path.join(directory, latest_file)
            logger.warning(f"  loading most recent version:\n\n    {filepath}\n\n")
            with open(filepath, 'r') as f:
                app_data: dict = json.load(f)
            return app_data

