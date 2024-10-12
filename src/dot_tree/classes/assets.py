import os
import re
import sys
import json
import builtins
import logging
import keyword
import appdirs
import traceback
import unicodedata
logger = logging.getLogger(__name__)



def is_reserved(name):
    if keyword.iskeyword(name) or name in dir(builtins):
        return True


class DirectoryNotEmptyError(OSError):
    def __init__(self, *args):
        super().__init__(*args)


def _excepthook(exc_type, exc_value, exc_traceback):
    """
        I hate how the core error message butts right up against
        the end of the trace dump, so this override puts some
        distance between the trace and the relevant error message
    """
    subclasses = [
        FileNotFoundError,
        AttributeError,
        DirectoryNotEmptyError,
        IsADirectoryError,
        NotADirectoryError
    ]

    def _is_subclass(exc_type):
        for subclass in subclasses:
            if issubclass(exc_type, subclass):
                return True
        return False

    if _is_subclass(exc_type):
        traceback.print_tb(exc_traceback)
        print(f"\n\n\n\n  {exc_type.__name__}: {exc_value}\n")
    else:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = _excepthook



class DotTreeBranch(os.PathLike):

    def __init__(self,
                 py_name,
                 os_name,
                 path,
                 dot_path,
                 parent,
                 trunk,
                 is_file=False,
                 extension=None):
        self.parent = parent
        self.trunk = trunk
        self.py_name = py_name
        self.os_name = os_name
        self.path = path
        self.dot_path = dot_path
        self.children = {}
        self.files_base_name = {}
        self.files = {}
        self._cached_asset = None
        self.is_file = is_file
        self.extension = extension
        self.extension_referenced = False
        self.is_shortcut = False

    def __str__(self):
        if not self.extension_referenced and self.is_file and not self.is_shortcut:
            dot_path = self.dot_path
            if self.dot_path.split('.')[-1] == self.extension:
                dot_path = '.'.join(self.dot_path.split('.')[:-1])
            output = f"Files must include extension, if they have one:\n\n"
            output += f"  {dot_path}.{'_'*len(self.extension)}\n"
            output += f"{' ' * (len(self.dot_path)-1)}{'^' * len(self.extension)}"
            raise AttributeError(output)
        self.extension_referenced = False
        return str(self.path)

    def __fspath__(self):
        return self.__str__()

    @staticmethod
    def _touch(filepath):
        with open(filepath, 'a'):
            os.utime(filepath, None)

    @staticmethod
    def _mkdir(path):
        os.mkdir(path)

    def eject(self, node):
        py_name = node.py_name
        file_key = py_name
        if node.is_file and node.extension is not None:
            file_key = f"{py_name}.{node.extension}"
        base_name = py_name.strip().lower()
        if node.is_file and '.' in py_name:
            base_name = py_name.split('.')[0].strip().lower()
        if base_name in self.files_base_name:
            del self.files_base_name[base_name]
        if node.os_name in self.trunk.name_mappings:
            del self.trunk.name_mappings[node.os_name]
        if file_key in self.files:
            del self.files[file_key]
        if py_name in self.children:
            del self.children[py_name]
        del node

    def rm(self, filename: str | None = None):
        from_self = False
        if filename is None:
            node = self
            from_self = True
        else:
            _filename = DotTree.normalize_name(filename)
            if _filename is not None:
                _filename = _filename.lower()
            node = self.files.get(_filename)
            if not node:
                node = self.children.get(_filename)

        if not node:
            raise FileNotFoundError(f"File not found: {filename}")

        if not node.is_file:
            dot_path = self.dot_path
            if from_self:
                dot_path = self.parent.dot_path
            syntax = f"  {dot_path}.{node.py_name}.rmdir()\n"
            syntax += f"\n    {dot_path}.rmdir('{node.py_name}')"
            raise IsADirectoryError(
                f"Can only delete files with rm().\n\n  This node is a directory: "
                f"{node.path}{os.path.sep}\n\n  "
                f"Please use rmdir() for directories:\n\n  {syntax}")

        if os.path.exists(node.path):
            os.remove(node.path)
        self.eject(node)

    delete = rm
    erase = rm
    remove = rm


    def rmdir(self, directory_name: str = None):
        from_self = False
        if directory_name is None:
            node = self
            from_self = True
        else:
            _directory_name = DotTree.normalize_name(directory_name)
            if _directory_name is not None:
                _directory_name = _directory_name.lower()
            node = self.children.get(_directory_name)
            if not node:
                node = self.files.get(_directory_name)

        if not node:
            raise FileNotFoundError(f"Directory not found: {directory_name}")

        if node.is_file:
            dot_path = self.dot_path
            if from_self:
                dot_path = self.parent.dot_path
            syntax = f"  {dot_path}.{node.py_name}.{node.extension}.rm()\n"
            syntax += f"\n    {dot_path}.rm('{node.py_name}.{node.extension}')"
            raise NotADirectoryError(
                f"Can only delete directories with rmdir().\n\n  This node is a file: {node.path}"
                f"\n\n  Use rm() for files.\n\n  {syntax}")

        files = [f for f in os.listdir(node.path)]
        if len(files) > 0:
            aggs = node.tree(to_stdout=False)
            raise DirectoryNotEmptyError(f"Can only delete empty directories.\n\n"
                                         f"  Directory: {node.path}\n\n  "
                                         f"Currently contains: {len(files)} file(s):"
                                         f"\n\n{aggs}")
        if os.path.exists(node.path):
            os.rmdir(node.path)
        self.eject(node)

    rd = rmdir

    def touch(self, filename):
        if is_reserved(filename):
            raise Exception(f"Error: '{filename}' is a reserved python keyword.  "
                            "Please choose a different name.")
        filepath = os.path.join(self.path, filename)
        self._touch(filepath)
        return self.add_child_file(filename, filepath)

    def add_child_file(self, filename, child_path):
        py_name = DotTree.normalize_name(filename)
        py_name = py_name.lower()
        child_dot_path = f"{self.dot_path}.{py_name}"
        if '.' in py_name:
            base_name = py_name.split('.')[0].strip().lower()
            extension = py_name.split('.')[1].strip().lower()
        else:
            base_name = py_name.strip().lower()
            extension = None
        file = DotTreeBranch(base_name,
                             filename,
                             child_path,
                             child_dot_path,
                             parent=self,
                             trunk=self.trunk,
                             extension=extension,
                             is_file=True)
        self.files_base_name[base_name] = file
        self.files[py_name] = file
        shortcut = DotTreeBranch(base_name,
                                 filename,
                                 child_path,
                                 child_dot_path,
                                 parent=self,
                                 trunk=self.trunk,
                                 extension=extension,
                                 is_file=True)
        shortcut.is_shortcut = True
        file.children = shortcut.children
        file.files_base_name = shortcut.files_base_name
        file.files = shortcut.files
        return shortcut

    def mkdir(self, node):
        if is_reserved(node):
            raise Exception(f"Error: '{node}' is a reserved python keyword.  "
                            "Please choose a different name.")
        child_path = os.path.join(self.path, node)
        self._mkdir(child_path)
        return self.add_child_directory(node, child_path)


    def add_child_directory(self, node, child_path):
        py_name = DotTree.normalize_name(node)
        py_name = py_name.lower()
        child_dot_path = f"{self.dot_path}.{py_name}"
        subdir = DotTreeBranch(py_name,
                               node,
                               child_path,
                               child_dot_path,
                               parent=self,
                               trunk=self.trunk)
        self.children[py_name] = subdir
        return subdir

    def get_size(self,
                 units='auto',
                 return_only_value=False,
                 child=False,
                 to_stdout=True):
        if not units:
            raise Exception("\n\n\n    Units must be: auto, B, KB, MB, GB, or TB.\n")
        size: float = 0
        if self.is_file:
            size = os.path.getsize(self.path)
        else:
            for file in self.files.values():
                size += file.get_size(child=True, to_stdout=to_stdout)
            for subdir in self.children.values():
                size += subdir.get_size(child=True, to_stdout=to_stdout)
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
            self.is_shortcut = True
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

        joined = f"File or folder not found:\n\n  {self.dot_path}.{raw_name}\n"
        joined += f"{' ' * (len(self.dot_path))}   {'^' * len(raw_name)}\n"

        files = [f for f in os.listdir(self.path)]
        lpad = 0
        if files:
            joined += f"  Files in {self.path}:\n\n"
            lpad = len(max(files, key=len))
            for file in files:
                norm_name = DotTree.normalize_name(file).lower()
                joined += f"  .{os.path.sep}{file.ljust(lpad, ' ')}"
                joined += f"  {self.dot_path}.{norm_name}\n"
        else:
            joined += f"  No files found in {self.path}"
        raise FileNotFoundError(f"[Errno 2] {joined}")

    def __getitem__(self, key):
        if key in self.children:
            return self.children[key]
        elif key in self.files:
            return self.files[key]
        self.__getattr__(key)

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
            if os.path.isdir(child_path):
                subdir = self.add_child_directory(node, child_path)
                subdir.build_tree(child_path)
            else:
                self.add_child_file(node, child_path)

    def load(self, mode='auto', decode: str = None):
        if not self.is_file:
            files = []
            for file in self.files.values():
                files.append(file.load())
            return files
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

    def show_tree(self, node=None, to_stdout=True):
        if not node:
            node = self
        if self.is_file:
            logger.warning(f"\n\n  show_tree() is for directory nodes.\n\n  "
                           f"This node is a file: {self.os_name}\n\n")
            return ''
        return self.parent.show_tree(node=node, to_stdout=to_stdout)
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
    dir = list


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
        self.dot_path = '<DotTree>'
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

        joined = f"File or folder not found:\n\n  "
        joined += f"{self.dot_path}.{raw_name}\n"
        joined += f"{' ' * (len(self.dot_path))}   "
        joined += f"{'^' * len(raw_name)}\n"
        joined += f"  Files in {self.path}:\n"
        files = [f for f in os.listdir(self.path)]
        lpad = len(max(files, key=len))
        joined += f"\n    {'File'.ljust(lpad, ' ')}    Python Syntax"
        for file in files:
            norm_name = DotTree.normalize_name(file).lower()
            joined += f"\n    .{os.path.sep}{file.ljust(lpad, ' ')}  "
            joined += f"{self.dot_path}.{norm_name}"
        raise FileNotFoundError(f"[Errno 2] {joined}")

    def __getitem__(self, raw_key):
        key = raw_key.strip().lower()
        if key in self.children:
            return self.children[key]
        if key in self.files:
            return self.files[key]
        if key in self.files_base_name:
            return self.files_base_name[key]
        self.__getattr__(raw_key)

    def eject(self, node):
        py_name = node.py_name
        file_key = py_name
        if node.is_file and node.extension is not None:
            file_key = f"{py_name}.{node.extension}"
        base_name = py_name
        if node.is_file and '.' in py_name:
            base_name = py_name.split('.')[0].strip().lower()
        if base_name in self.files_base_name:
            del self.files_base_name[base_name]
        if node.os_name in self.name_mappings:
            del self.name_mappings[node.os_name]
        if file_key in self.files:
            del self.files[file_key]
        if py_name in self.children:
            del self.children[py_name]
        del node

    def rm(self, filename: str | None = None):
        from_self = False
        if filename is None:
            node = self
            from_self = True
        else:
            _filename = self.normalize_name(filename)
            if _filename is not None:
                _filename = _filename.lower()
            node = self.files.get(_filename)
            if not node:
                node = self.children.get(_filename)

        if not node:
            raise FileNotFoundError(f"File not found: {filename}")

        if not node.is_file:
            dot_path = self.dot_path
            if from_self:
                dot_path = self.parent.dot_path
            syntax = f"  {dot_path}.{node.py_name}.rmdir()\n"
            syntax += f"\n    {dot_path}.rmdir('{node.py_name}')"
            raise IsADirectoryError(
                f"{node.path}{os.path.sep}\n\n  Can only delete files with rm().  "
                f"This node is a directory.\n\n  "
                f"Please use rmdir() for directories:\n\n  {syntax}")

        if os.path.exists(node.path):
            os.remove(node.path)
        self.eject(node)

    delete = rm
    erase = rm
    remove = rm

    def rmdir(self, directory_name: str = None):
        from_self = False
        if directory_name is None:
            node = self
            from_self = True
        else:
            _directory_name = self.normalize_name(directory_name)
            if _directory_name is not None:
                _directory_name = _directory_name.lower()
            node = self.children.get(_directory_name)
            if not node:
                node = self.files.get(_directory_name)

        if not node:
            raise FileNotFoundError(f"Directory not found: {directory_name}")

        if node.is_file:
            dot_path = self.dot_path
            if from_self:
                dot_path = self.parent.dot_path
            syntax = f"  {dot_path}.{node.py_name}.{node.extension}.rm()\n"
            syntax += f"\n    {dot_path}.rm('{node.py_name}.{node.extension}')"
            raise NotADirectoryError(
                f"Can only delete directories.\n\n  This node is a file: {node.path}"
                f"\n\n  Please use rm() for files.\n\n  {syntax}")

        files = [f for f in os.listdir(node.path)]
        if len(files) > 0:
            aggs = node.tree(to_stdout=False)
            raise DirectoryNotEmptyError(f"Can only delete empty directories.\n\n"
                                         f"  Directory: {node.path}\n\n  "
                                         f"Currently contains: {len(files)} file(s):"
                                         f"\n\n{aggs}")
        if os.path.exists(node.path):
            os.rmdir(node.path)
        self.eject(node)
    rd = rmdir

    def get(self, key, default=None):
        if key in self.children:
            return self.children[key]
        elif key in self.files:
            return self.files[key]
        return default

    @staticmethod
    def _touch(filepath):
        with open(filepath, 'a'):
            os.utime(filepath, None)

    @staticmethod
    def _mkdir(path):
        os.mkdir(path)

    def touch(self, filename):
        if is_reserved(filename):
            raise Exception(f"Error: '{filename}' is a reserved python keyword.  "
                            "Please choose a different name.")
        filepath = os.path.join(self.path, filename)
        self._touch(filepath)
        return self.add_child_file(filename, self.path)

    def add_child_file(self, node, path):
        child_path = os.path.join(path, node)
        child_dot_path = f"{self.dot_path}.{self.normalize_name(node)}"
        py_name = self.normalize_name(node)
        if py_name != node:
            self.name_mappings.update({node: py_name})
        py_name = py_name.lower()
        if '.' in py_name:
            base_name = py_name.split('.')[0].strip().lower()
            extension = py_name.split('.')[1].strip().lower()
        else:
            base_name = py_name.strip().lower()
            extension = None
        if base_name[0:1].isnumeric():
            base_name = f"_{base_name}"
        file = DotTreeBranch(base_name,
                             node,
                             child_path,
                             child_dot_path,
                             parent=self,
                             trunk=self,
                             extension=extension,
                             is_file=True)
        self.files_base_name[base_name] = file
        self.files[py_name] = file
        shortcut = DotTreeBranch(base_name,
                                 node,
                                 child_path,
                                 child_dot_path,
                                 parent=self,
                                 trunk=self,
                                 extension=extension,
                                 is_file=True)
        shortcut.is_shortcut = True
        file.children = shortcut.children
        file.files_base_name = shortcut.files_base_name
        file.files = shortcut.files
        return shortcut

    def mkdir(self, node):
        if is_reserved(node):
            raise Exception(f"Error: '{node}' is a reserved python keyword.  "
                            "Please choose a different name.")
        child_path = os.path.join(self.path, node)
        self._mkdir(child_path)
        return self.add_child_directory(node, child_path)

    def add_child_directory(self, node, child_path):
        child_dot_path = f"{self.dot_path}.{self.normalize_name(node)}"
        py_name = self.normalize_name(node)
        if py_name != node:
            self.name_mappings.update({node: py_name})
        py_name = py_name.lower()
        subdir = DotTreeBranch(py_name,
                               node,
                               child_path,
                               child_dot_path,
                               parent=self,
                               trunk=self)
        self.children[py_name] = subdir
        return subdir

    def build_tree(self, path):
        ignore_pattern = re.compile('|'.join(self.ignored_files))
        for node in os.listdir(path):
            if ignore_pattern.search(node):
                continue
            child_path = os.path.join(path, node)
            py_name = self.normalize_name(node)
            if py_name != node:
                self.name_mappings.update({node: py_name})
            if os.path.isdir(child_path):
                subdir = self.add_child_directory(node, child_path)
                subdir.build_tree(child_path)
            else:
                self.add_child_file(node, path)

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
                keys = [key for key in list(files.keys()) if key]
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

    def get_size(self,
                 units='auto',
                 return_only_value=False,
                 child=False,
                 to_stdout=True):

        if not units:
            raise Exception("\n\n\n    Units must be: auto, B, KB, MB, GB, or TB.\n")

        size: float = 0
        if self.is_file:
            size = os.path.getsize(self.path)
        else:
            for file in self.files.values():
                size += file.get_size(child=True, to_stdout=to_stdout)

            for subdir in self.children.values():
                size += subdir.get_size(child=True, to_stdout=to_stdout)

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
    dir = list

    def show_name_mappings(self):
        print('\n\n')
        for original, normalized in self.name_mappings.items():
            print(f"{original} -> {normalized}")
        print('\n\n')

    @staticmethod
    def normalize_name(original_name):
        if original_name is None:
            return None
        if is_reserved(original_name):
            original_name = f"_{original_name}"
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
          # output:
          # C:\dot_tree\src\dot_tree\assets\tiles\animated_orc\Walking\Orc_Walking.png

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



