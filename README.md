# DotTree

### A.Sugary.Python.Asset.Handler.py.load()

```python
pip install python-dot-tree
```

<hr>

DotTree simplifies the handling of assets on disk within Python projects that have a lot of assets, by handling the OS related nuances of paths, while allowing for direct case-insensitive dot-notation syntax in Python to represent your paths and filepaths.  It includes features for caching and precaching, as well as some convenience functions.  Also includes a bundled appdata manager that greatly simplifies loading and saving to data from the user-specific appdata location, completely in an operating system agnostic manner. 

<hr>

### Features

- uses dot-notation, so your code resembles the actual paths
- handles underlying paths for your OS, making your code operating system agnostic
- due to the dot notation and python object reference copies, you can [save any branch/node into its own variable](#shortcuts) to use as a shortcut
- has built-in functions to help with development: [.tree()](#tree), [.ls()](#ls), [.size()](#size)
- automatically caches, so reloading the same file later pulls from memory
- preload any part of the tree with [.preload()](#preloading) to avoid performance stutters and lag when lazy-loading assets
- [print your dot notation path representation](#string-representation) and the output will be the actual full OS path
- the dot notation path is a path-like derivative, so you can [directly use it to access files](#use-as-literal-path) in other modules
- unload a single asset or branch using `.unload()` when memory is priority over caching
- the dot notation representation is not case-sensitive, so this simplifies typing a path regardless of the mixed case in your paths
- includes an [appdata interfacing class](#app-data-management) that greatly simplifies saving data to appdata, regardless of the underlying OS

<hr>

Let's look at an example.  Let's say we have this directory structure:
```
repo_name/
    assets/
        config/
            settings.conf
    services/
        example.py
```

```python
import os

self_path = os.path.dirname(os.path.abspath(__file__))
assets_path = os.path.join(self_path, "..", "assets")
config_filepath = os.path.join(assets_path, "config", "settings.conf")

with open(config_filepath, 'r') as fh:
    print(fh.read())
```

The above code isn't too bad for those familiar with Python.  The syntax is a bit muddy with all of the path joins, but that's the best way to handle paths in Python when you're making a project that you intend to be run on any operating system.  The above settings path would be something like '../assets/config/settings.conf' in Linux or Mac OS.  The above code doesn't really give you the sense of this due to the extra syntactical fluff that relying on os.path modules adds.

DotTree changes this.  Let's do the identical to the above:
```python
from dot_tree import DotTree
assets = DotTree("../assets")

print(assets.config.settings.conf.load())
```

That's it.  Also notice how our reference to the file in the actual code resembles what the actual path is in reality?

This module is basically syntactical sugar for accessing files on disk, without added complexity or fluff.  There are a few minor limitations however, related to python naming rules, and you can read about those [here](#limitations-of-dottree). 

I made this for myself while I was working on a PyGame project, but decided to pull the PyGame stuff out and put that in a separate class extension, so I can put the base class out there for anyone that wants to tinker with it.

As for the included PyGame extension of this module, here's an example of loading all parallax background images from a directory, then into PyGame surface instances, put into a python list, immediately ready for use in a parallax background class, using this module:
```python
from dot_tree import GameDotTree

assets = GameDotTree("../assets")
backgrounds = assets.backgrounds.parallax_forest.load(scaled_height=screen.height)
```

Ignoring the import statement, only two lines of code here are for loading the images, and only the last line is actually doing the loading.  The first line is just instantiating DotTree, so once it's up and running, you can access and load files with a single line of code using dot-notation.

Here's the same code as above, functionally, but without using this module to simplify the process.  This example isn't even doing the math to scale the image when it's not the same aspect as the screen like the above implementation does.  That would make this even longer.
```python
import os

self_path = os.path.dirname(os.path.abspath(__file__))
assets_path = os.path.join(self_path, "..", "assets")
backgrounds_path = os.path.join(assets_path, "backgrounds", "parallax_forest")

image_extensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']

files = os.listdir(backgrounds_path)
backgrounds = []
for file in files:
    if file[-3:] in image_extensions or file[-4:] in image_extensions:
        path = os.path.join(backgrounds_path, file)
        surface = pygame.image.load(path)
        surface.convert_alpha()
        resized_surface = pygame.transform.scale(surface, (800, 600))
        backgrounds.append(resized_surface)
```

Quite a difference in legibility of the code, yeah?

`DotTree` has several built-in convenience features that can speed up development.  

Operating systems don't usually have a good way to summarize a directory tree, and by that, I mean any directory listing or tree output would give you a row per file or directory, so with many files, you get a lot of output, which isn't always useful when you just need a summary.

With `DotTree` you can call .tree() on any directory node to get a tree output that groups files by type, and aggregates size and count, for both files and directories, recursively.  By default it outputs to stdout, but you can suppress it with an optional argument.  It also returns the tree if you need to capture it.

<hr>

### Tree

```python
assets = DotTree("/app/assets")
assets.tree()
'''
output:
 332.29 KB      platformer_assets/
  119.6 KB         BG/
  119.6 KB             *.png (1)
  65.35 KB         Object/
  65.35 KB             *.png (13)
 147.34 KB         Tiles/
 147.34 KB             *.png (18)
'''
```

<hr>

### String Representation

You can print a `DotTree` object to get the full OS path.
```python
assets = DotTree("/app/assets")
print(assets.sprites.player_1.jpg)
# output: /app/assets/sprites/player_1.jpg
```

<hr>

### Use as literal path

You can even use the `DotTree` path object directly as a path, as it's a path-like derived instance.  `DotTree` is OS-agnostic, and will work regardless of the underlying operating system.
```python
assets = DotTree("/app/assets")

with open(assets.about.txt, 'r') as fh:
    print(fh.read())
```

<hr>

### ls

You can run .ls() to get a list of files and directories.  Directories will have a trailing slash.  This returns a python list.
```python
print(assets.sprites.ls())
# output: ['thumbnails/', 'player_1.jpg', 'player_2.jpg', 'player_3.jpg', 'player_4.jpg']
```

<hr>

### size

You can get the size of a single file or directory (cumulative if it's a directory), by calling .size() on it.
```python
assets = GameDotTree("/app/assets")
assets.main_logo.jpg.size()  # file
# output: 332.29 KB

assets.size()  # directory
# output: 34.11 MB
```

<hr>

### Shortcuts

Due to `Dot.Tree` using nested objects, and due to how python copies objects by reference if you don't explicitly do a copy, you can make shortcut variables for any node in the tree to reference to shorten code.

```python
assets = GameDotTree("/app/assets")

img = assets.continent_3.zone_1.city_2.dungeon_5.sprites
music = assets.continent_3.zone_1.city_2.dungeon_5.music

boss = img.first_boss.png.load()
minion_1 = img.minion_1.png.load()
minion_2 = img.minion_2.png.load()
imp_1 = img.imp_1.png.load()
imp_2 = img.imp_2.png.load()
ghost = img.ghost.png.load()
flame = img.flame.png.load()

dungeon_theme_1 = music.dungeon_theme_1.wav.load()
dungeon_theme_2 = music.dungeon_theme_2.wav.load()
dungeon_theme_3 = music.dungeon_theme_3.wav.load()
```

In the above example, if you didn't save the branch into the shortcut variable, the full path syntax would have been:
```python
assets = GameDotTree("/app/assets")

boss = assets.continent_3.zone_1.city_2.dungeon_5.sprites.first_boss.png.load()
minion_1 = assets.continent_3.zone_1.city_2.dungeon_5.sprites.minion_1.png.load()
minion_2 = assets.continent_3.zone_1.city_2.dungeon_5.sprites.minion_2.png.load()
imp_1 = assets.continent_3.zone_1.city_2.dungeon_5.sprites.imp_1.png.load()
imp_2 = assets.continent_3.zone_1.city_2.dungeon_5.sprites.imp_2.png.load()
ghost = assets.continent_3.zone_1.city_2.dungeon_5.sprites.ghost.png.load()
flame = assets.continent_3.zone_1.city_2.dungeon_5.sprites.flame.png.load()

dungeon_theme_1 = assets.continent_3.zone_1.city_2.dungeon_5.music.dungeon_theme_1.wav.load()
dungeon_theme_2 = assets.continent_3.zone_1.city_2.dungeon_5.music.dungeon_theme_2.wav.load()
dungeon_theme_3 = assets.continent_3.zone_1.city_2.dungeon_5.music.dungeon_theme_3.wav.load()
```

That obviously can save a lot on code length and typing time, especially when you're loading many files from a single directory.

You can shorten it some more by using load() on the music directory to return a list of the music files in that directory.  This is especially handy when you have a directory that contains related objects you need to load all of.  This feature only works for the PyGame specific class extension, `GameDotTree`, and it only works for images, sound files, and fonts that are supported formats of PyGame.

```python
import pygame
dungeon_themes = assets.continent_3.zone_1.city_2.dungeon_5.music.load()

print(len(dungeon_themes))
# output: 3

print(type(dungeon_themes[0]))
# output: <class 'pygame.mixer.Sound'>
```

Regarding PyGame specifically, fonts automatically load into PyGame Font objects, images load as PyGame surface objects, and sounds and music get loaded as PyGame mixer objects.  Use the base class if you need to load those types as simply binary.

## Preloading

When you know you're about to access specific files, specifically a specific branch, if your assets are organized in such a way, you can use `.preload()` on a directory node to recursively preload/precache all assets from that node and lower.  

This prevents stutters and lag from lazy-loading assets on the fly directly from disk.  Cached assets load from memory when `.load()` is called on them, making them load instantly.

```python
assets.continent_3.zone_1.dungeon_5.preload()
```

Doing `.preload()` means the pygame objects are already created, so when you do a `.load()` on any given file node contained within it, it'll load immediately.  If you lazy load without precaching, you can get microstutters, since python is tied to the global interpreter lock, and disk IO is slow and can block your game loop.

If you use the base `Dot.T class and do a load(), you'll still get caching, but it will store the file as a binary object in memory, instead of PyGame objects.  It does attempt to detect the filetype and use text mode when it knows to, but you can specify with using the mode argument, which is the same as using python's open() function.  'r' for reading text, and 'rb' for reading binary.  If you don't specify, it attempts to auto-detect depending on the file extension.

<hr>

### Limitations of DotTree

DotTree uses nested objects to achieve the dot notation support to syntactically represent your asset tree.

The one downside to this is python naming limitations.  Luckily they've been accounted for, so even if you run into some, you can choose to use the work-around instead of renaming problem directories or files.

1. names of files or directories starting with a number.  python doesn't allow this, so you can either rename your file or directory, or add an underscore before the number.  the module will still reference the real full OS path internally, but you can prepend an underscore in your dot notation to reference files that start with a number
   ```python
   # filename in OS: assets/sprites/1.png
   
   # solution: add underscore before the filename in python:
   assets.sprites._1.png
   ```
2. names of files or directories containing spaces.  python doesn't allow spaces in object names, so spaces get replaced with underscores for referencing.  internally, `DotTree` still references the full actual OS path, but for referencing it via dot notation, just replace the space with underscores
   ```python
   # filename in OS: assets/sprites/first boss.jpg
   
   # solution: replace spaces with underscores in python
   assets.sprites.first_boss.jpg
   ```
3. periods and hyphens in filenames or directory names will not work, as periods are a part of python syntax, and hyphens aren't allowed in python class names.  the resolution is to replace both with underscores
   ```python
   # filename in OS: assets/sprites/brill.innkeeper-1.gif
   
   # solution: replace hyphens and periods with underscores in python
   assets.sprites.brill_innkeeper_1.gif
   ```
4. special characters that the operating system might allow, but python class names don't, like parenthesis and braces and other non-alphanumeric characters.  the solution is to just remove them.  don't forget though; spaces, hyphens, and periods need to be changed to underscores, but all others need to just be removed
   ```python
   # filename in OS: assets/sprites/tree [brown] (1).tif
   
   # solution: replace spaces with underscores and remove brackets and parenthesis in python
   assets.sprites.tree_brown_1.tif
   ```

It's better to have clean naming standards with file and directory naming, so I personally don't find these minor limitations to be restrictive for my current use, but for those that prefer not to rename assets, they can simply use the above workaround.

Here's a real example in one of my local projects:
```python
# actual OS path: assets\platformer_assets2\2015-02-26 [DB32](Generic Platformer)(Clouds).png

img = assets.platformer_assets2._2015_02_26_db32generic_platformerclouds.png
img.size()
# output: 1.61 KB
```

And while that's an intentionally extreme example I hand-picked, I think that most would agree that while the workaround did its job, it would be better to simply use cleaner naming:
```shell
mv 2015-02-26\ [DB32](Generic\ Platformer)(Clouds).png generic_platformer_clouds.png
```

No workaround needed and everyone lives happily ever after:
```python
assets.platformer_assets2.generic_platformer_clouds.png
```

On the other hand, `DotTree` is not case-sensitive, so that is convenient for those that dislike mixed case names.

<hr>

## App Data Management

A module already exists to make interfacing with Windows, Linux, and Mac OS app data directories easier, but included in `DotTree` are a couple classes that simplify the usage a bit.  This is a wrapper for that module: [appdirs python module](https://pypi.org/project/appdirs/).

The PyGame specific extension of this appdata class even creates a screenshots directory in the user's local appdata directory automatically.  That means if you incorporate the appdata manager in your app, you'll always have a place to dump screenshots the user captures in game.  You can also store game state, high scores, user preferences, configuration, logs, and more, and simply give the class methods the dictionary you want to save, and it handles everything else for you.  The files are stored on disk in JSON format, so you can view and edit the files as needed.  The most basic use is to store everything in a dictionary and then use `.load()` and `.save()`.  If you want granular and compartmentalized storage, there are separate methods for various things, supported by the underlying appdirs module: data, config, cache, state, and log.  The PyGame specific extension also adds screenshot methods, which I suppose you could use for storing metadata about screenshots you've taken and stored, but if you don't, you can just grab the full OS path to the screenshots directory from the screenshots_path instance method and dump your screenshots there without logging any metadata about them.

Here's an example of how you can save a user's preferences.  The first argument is the name of the app, and the second argument is the app username.  This is for allowing multiple users of your app (for a single OS user), allowing each to retain their own settings.  If you don't provide a user, it has a default value, so the app name is all you have to supply.  Separate operating system users get their own home directory where app data directories are usually stored, so each OS user gets their own data by default.
```python
from dot_tree import AppData

appdata = AppData('MyAppName')

# save some data
user_preferences = {'ui_mode': 'dark'}
appdata.save(user_preferences)

# load data
user_preferences = appdata.load()
ui_mode = user_preferences.get('ui_mode')
```

If your game or app has more than one user, you can pass in the second optional user argument to store them individually.
```python
from dot_tree import AppData

appdata = AppData('MyAppName', 'UserOfYourApp')
```

The PyGame specific extension of this class adds a screenshot directory within app data, and the path to it can be retrieved using the screenshots_path instance variable, so you can use that as the location to write screenshots within your game with no work required, as the underlying appdirs module handles the logistics.

The app data directories are most often these locations:

- **macOS**:
  - `~/Library/Application Support/<app_name>`

- **Linux/Unix**:
  - `~/.local/share/<app_name>`

- **Windows XP**:
  - `C:\Documents and Settings\<windows_username>\Application Data\<app_name>`

- **Windows 7+**:
  - `C:\Users\<windows_username>\AppData\Local\<app_author>\<app_name>`

<hr>

There's a lot of info about the app data stuff in the [docstring](https://github.com/nebko16/dot_tree/blob/5d7b8a7515069e799e3d4eaa577672ffe3804042/src/dot_tree/classes/assets.py#L586), so you can go get all the details there, or you can also check out the [module that this is a wrapper for](https://pypi.org/project/appdirs/). 
