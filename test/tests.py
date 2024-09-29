import os
import pygame
import unittest
from dot_tree import DotTree, GameDotTree, AppData, GameData
pygame.init()
pygame.display.set_mode((100, 100))


class TestDotTree(unittest.TestCase):

    def test_instantiate(self):
        assets = DotTree('assets')
        self.assertIsInstance(assets, DotTree)

    def test_load_textfile(self):
        assets = DotTree('assets')
        contents = assets.test_config.txt.load()
        self.assertEqual(contents, 'goodbye mars')

    def test_load_filename_number_first_letter(self):
        assets = DotTree('assets')
        contents = assets._1_test.txt.load()
        self.assertEqual(contents, 'entropy')

    def test_load_filename_spaces_hyphen(self):
        assets = DotTree('assets')
        contents = assets._1_bad_file_name.txt.load()
        self.assertEqual(contents, 'plurality')

    def test_file_no_extension(self):
        assets = DotTree('assets')
        contents = assets.extensionless.load(mode='r')
        self.assertEqual(contents, 'exhibition')

    def test_file_load_from_parent(self):
        assets = DotTree('assets')
        contents = assets.subdir.load()
        self.assertEqual(contents[0], 'test')

    def test_nested_file(self):
        assets = DotTree('assets')
        contents = assets.subdir.file.txt.load()
        self.assertEqual(contents, 'test')

    def test_preload(self):
        assets = DotTree('assets')
        assets.subdir.preload()
        self.assertEqual(assets.subdir.file.txt._cached_asset, 'test')

    def test_uncache(self):
        assets = DotTree('assets')
        assets.subdir.file.txt.load()
        assets.subdir.file.txt.unload()
        self.assertIsNone(assets.subdir.file.txt._cached_asset)

    def test_str_path(self):
        assets = DotTree('assets')
        path = str(assets.subdir.file.txt).split('test')[-1]
        path = '.'.join(path.split(os.path.sep))
        self.assertEqual(path, '.assets.subdir.file.txt')

    def test_ls(self):
        assets = DotTree('assets')
        contents = assets.subdir.ls()
        contents.sort()
        self.assertEqual(contents, ['file.txt', 'subterranean/'])

    def test_tree(self):
        assets = DotTree('assets')
        contents = assets.subdir.tree(to_stdout=False)
        output = '''       0 B   subterranean/
       4 B    *.txt (1)'''
        self.assertEqual(contents, output)

    def test_size(self):
        assets = DotTree('assets')
        contents = assets.subdir.file.txt.size(to_stdout=False, units='B')
        self.assertEqual(contents, '4 B')

    def test_tree_as_path(self):
        assets = DotTree('assets')
        with open(assets.subdir.file.txt, 'r') as fh:
            contents = fh.read()
        self.assertEqual(contents, 'test')

    def test_file_not_found_print(self):
        assets = DotTree('assets')
        with self.assertRaises(FileNotFoundError):
            print(assets.subdir.does_not_exist.txt)

    def test_file_not_found_call(self):
        assets = DotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.subdir.does_not_exist.txt.load()

    def test_directory_not_found_print(self):
        assets = DotTree('assets')
        with self.assertRaises(FileNotFoundError):
            print(assets.this_dir_does_not_exist)

    def test_directory_not_found_call(self):
        assets = DotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.this_dir_does_not_exist.ls()


class TestGameDotTree(unittest.TestCase):

    def test_instantiate(self):
        assets = GameDotTree('assets')
        self.assertIsInstance(assets, DotTree)

    def test_load_textfile(self):
        assets = GameDotTree('assets')
        contents = assets.test_config.txt.load()
        self.assertEqual(contents, 'goodbye mars')

    def test_load_filename_number_first_letter(self):
        assets = GameDotTree('assets')
        contents = assets._1_test.txt.load()
        self.assertEqual(contents, 'entropy')

    def test_load_filename_spaces_hyphen(self):
        assets = GameDotTree('assets')
        contents = assets._1_bad_file_name.txt.load()
        self.assertEqual(contents, 'plurality')

    def test_file_no_extension(self):
        assets = GameDotTree('assets')
        contents = assets.extensionless.load(mode='r')
        self.assertEqual(contents, 'exhibition')

    def test_file_load_from_parent(self):
        assets = GameDotTree('assets')
        contents = assets.subdir.load()
        self.assertEqual(contents[0], 'test')

    def test_nested_file(self):
        assets = GameDotTree('assets')
        contents = assets.subdir.file.txt.load()
        self.assertEqual(contents, 'test')

    def test_preload(self):
        assets = GameDotTree('assets')
        assets.subdir.preload()
        self.assertEqual(assets.subdir.file.txt._cached_asset, 'test')

    def test_uncache(self):
        assets = GameDotTree('assets')
        assets.subdir.file.txt.load()
        assets.subdir.file.txt.unload()
        self.assertIsNone(assets.subdir.file.txt._cached_asset)

    def test_str_path(self):
        assets = GameDotTree('assets')
        path = str(assets.subdir.file.txt).split('test')[-1]
        path = '.'.join(path.split(os.path.sep))
        self.assertEqual(path, '.assets.subdir.file.txt')

    def test_ls(self):
        assets = GameDotTree('assets')
        contents = assets.subdir.ls()
        contents.sort()
        self.assertEqual(contents, ['file.txt', 'subterranean/'])

    def test_tree(self):
        assets = GameDotTree('assets')
        contents = assets.subdir.tree(to_stdout=False)
        output = '''       0 B   subterranean/
       4 B    *.txt (1)'''
        self.assertEqual(contents, output)

    def test_size(self):
        assets = GameDotTree('assets')
        contents = assets.subdir.file.txt.size(to_stdout=False, units='B')
        self.assertEqual(contents, '4 B')

    def test_tree_as_path(self):
        assets = GameDotTree('assets')
        with open(assets.subdir.file.txt, 'r') as fh:
            contents = fh.read()
        self.assertEqual(contents, 'test')

    def test_file_not_found_print(self):
        assets = GameDotTree('assets')
        with self.assertRaises(FileNotFoundError):
            print(assets.subdir.does_not_exist.txt)

    def test_file_not_found_call(self):
        assets = GameDotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.subdir.does_not_exist.txt.load()

    def test_directory_not_found_print(self):
        assets = GameDotTree('assets')
        with self.assertRaises(FileNotFoundError):
            print(assets.this_dir_does_not_exist)

    def test_directory_not_found_call(self):
        assets = GameDotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.this_dir_does_not_exist.ls()

    def test_load_image(self):
        assets = GameDotTree('assets')
        image = assets.images.small.png.load()
        self.assertIsInstance(image, pygame.Surface)
        self.assertEqual(image.get_rect(), (0, 0, 123, 456))
        assets.images.small.png.unload()
        self.assertIsNone(assets.images.small.png._cached_asset)

    def test_load_image_from_parent(self):
        assets = GameDotTree('assets')
        images = assets.images.load()
        _l = '[<Surface(1234x5678x32, global_alpha=255)>, <Surface(123x456x32, global_alpha=255)>]'
        self.assertEqual(str(images), _l)
        self.assertIsInstance(images, list)
        self.assertEqual(len(images), 2)

    def test_branch_preload(self):
        assets = GameDotTree('assets')
        assets.preload()
        self.assertNotEqual(assets.images.small.png._cached_asset, None)
        self.assertIsInstance(assets.images.small.png._cached_asset, pygame.Surface)

    def test_load_mixer(self):
        assets = GameDotTree('assets')
        sound = assets.audio.sound.wav.load()
        self.assertIsInstance(sound, pygame.mixer.Sound)

    def test_load_font(self):
        assets = GameDotTree('assets')
        font = assets.fonts.ps2p.ttf.load()
        self.assertIsInstance(font, pygame.font.Font)


# todo: test AppData
#       test GameData




if __name__ == '__main__':

    unittest.main()


pygame.quit()
