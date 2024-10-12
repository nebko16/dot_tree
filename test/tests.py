import os
import pygame
import unittest
from dot_tree import DotTree, GameDotTree
from dot_tree import DirectoryNotEmptyError
pygame.init()
pygame.display.set_mode((100, 100))

# todo: test AppData & GameData too?
#       check python keywords for create dir/file methods
#       add error message for reserved keywords


def cleanup():
    self_path = os.path.abspath(os.path.dirname(__file__))
    test_assets = os.path.join(self_path, 'assets')

    files = [
        os.path.join(test_assets, 'file.txt'),
        os.path.join(test_assets, 'subdir2', 'file2.txt'),
        os.path.join(test_assets, 'subdir4', 'subdir', 'file.txt'),
        os.path.join(test_assets, 'subdir5', 'subdir', 'file.txt'),
    ]
    dirs = [
        os.path.join(test_assets, 'subdir0', 'subdir2'),
        os.path.join(test_assets, 'subdir3', 'subdir'),
        os.path.join(test_assets, 'subdir4', 'subdir'),
        os.path.join(test_assets, 'subdir5', 'subdir'),
        os.path.join(test_assets, 'subdir'),
        os.path.join(test_assets, 'subdir2'),
        os.path.join(test_assets, 'subdir3'),
        os.path.join(test_assets, 'subdir4'),
        os.path.join(test_assets, 'subdir5'),
    ]
    for file in files:
        if os.path.exists(file):
            os.remove(file)
    for _dir in dirs:
        if os.path.exists(_dir):
            os.rmdir(_dir)


class TestDotTree(unittest.TestCase):

    def setUp(self):
        cleanup()

    def test_rm_trunk_file_from_parent(self):
        assets = DotTree('assets')
        assets.touch('file.txt')
        path = str(assets.file.txt)
        assets.rm('file.txt')
        self.assertFalse(os.path.exists(path))

    def test_rm_trunk_file_from_self(self):
        assets = DotTree('assets')
        assets.touch('file.txt')
        path = str(assets.file.txt)
        assets.file.txt.rm()
        self.assertFalse(os.path.exists(path))

    def test_rm_node_file_from_parent(self):
        assets = DotTree('assets')
        assets.subdir0.touch('file2.txt')
        path = str(assets.subdir0.file2.txt)
        assets.subdir0.rm('file2.txt')
        self.assertFalse(os.path.exists(path))

    def test_rm_node_file_from_self(self):
        assets = DotTree('assets')
        assets.subdir0.touch('file3.txt')
        path = str(assets.subdir0.file3.txt)
        assets.subdir0.file3.txt.rm()
        self.assertFalse(os.path.exists(path))

    def test_not_exist_rm_trunk_file_from_parent(self):
        assets = DotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.rm('i_do_not_exist.txt')

    def test_not_exist_rm_trunk_file_from_self(self):
        assets = DotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.i_do_not_exist.txt.rm()

    def test_not_exist_rm_file_from_self(self):
        assets = DotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.subdir0.i_do_not_exist.txt.rm()

    def test_not_exist_rm_file_from_parent(self):
        assets = DotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.subdir0.rm('i_do_not_exist.txt')

    def test_rm_trunk_dir_from_parent(self):
        assets = DotTree('assets')
        assets.mkdir('subdir')
        path = str(assets.subdir)
        assets.rmdir('subdir')
        self.assertFalse(os.path.exists(path))

    def test_rm_trunk_dir_from_self(self):
        assets = DotTree('assets')
        assets.mkdir('subdir')
        path = str(assets.subdir)
        assets.subdir.rmdir()
        self.assertFalse(os.path.exists(path))

    def test_rm_node_dir_from_parent(self):
        assets = DotTree('assets')
        assets.subdir0.mkdir('subdir')
        path = str(assets.subdir0.subdir)
        assets.subdir0.rmdir('subdir')
        self.assertFalse(os.path.exists(path))

    def test_rm_node_dir_from_self(self):
        assets = DotTree('assets')
        assets.subdir0.mkdir('subdir')
        path = str(assets.subdir0.subdir)
        assets.subdir0.subdir.rmdir()
        self.assertFalse(os.path.exists(path))

    def test_fail_rm_trunk_dir_not_empty_from_parent(self):
        assets = DotTree('assets')
        with self.assertRaises(DirectoryNotEmptyError):
            assets.rmdir('subdir0')
        with self.assertRaises(DirectoryNotEmptyError):
            assets.subdir0.rmdir()

    def test_fail_rm_node_dir_not_empty_from_parent(self):
        assets = DotTree('assets')
        with self.assertRaises(DirectoryNotEmptyError):
            assets.subdir0.rmdir('subterranean')
        with self.assertRaises(DirectoryNotEmptyError):
            assets.subdir0.subterranean.rmdir()

    def test_fail_rm_dir_from_trunk(self):
        assets = DotTree('assets')
        with self.assertRaises(IsADirectoryError):
            assets.subdir0.rm()
        with self.assertRaises(IsADirectoryError):
            assets.rm('subdir0')

    def test_fail_rmdir_file_from_trunk(self):
        assets = DotTree('assets')
        with self.assertRaises(NotADirectoryError):
            assets.test_config.txt.rmdir()
        with self.assertRaises(NotADirectoryError):
            assets.rmdir('test_config.txt')

    def test_fail_rm_dir_from_node(self):
        assets = DotTree('assets')
        with self.assertRaises(IsADirectoryError):
            assets.subdir0.subterranean.rm()
        with self.assertRaises(IsADirectoryError):
            assets.subdir0.rm('subterranean')

    def test_fail_rmdir_file_from_node(self):
        assets = DotTree('assets')
        with self.assertRaises(NotADirectoryError):
            assets.subdir0.file.txt.rmdir()
        with self.assertRaises(NotADirectoryError):
            assets.subdir0.rmdir('file.txt')

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
        contents = assets.subdir0.subterranean.load()
        self.assertEqual(contents[0], 'test')

    def test_nested_file(self):
        assets = DotTree('assets')
        contents = assets.test_config.txt.load()
        self.assertEqual(contents, 'goodbye mars')

    def test_create_directory_from_trunk(self):
        assets = DotTree('assets')
        assets.mkdir('subdir')
        self.assertTrue(os.path.exists(assets.subdir))

    def test_create_directory_from_branch(self):
        assets = DotTree('assets')
        assets.subdir0.mkdir('subdir2')
        self.assertTrue(os.path.exists(assets.subdir0.subdir2))

    def test_create_file_from_trunk(self):
        assets = DotTree('assets')
        assets.touch('file.txt')
        self.assertTrue(os.path.exists(assets.file.txt))

    def test_create_file_from_branch(self):
        assets = DotTree('assets')
        assets.subdir0.touch('file.txt')
        self.assertTrue(os.path.exists(assets.subdir0.file.txt))

    def test_chain_create_subdir_and_file(self):
        assets = DotTree('assets')
        with open(assets.mkdir('subdir2').touch('file2.txt'), 'w') as fh:
            fh.write('chain_test')
        contents = assets.subdir2.file2.txt.load()
        self.assertEqual(contents, 'chain_test')

    def test_chain_subdirs(self):
        assets = DotTree('assets')
        assets.mkdir('subdir3').mkdir('subdir')
        self.assertTrue(assets.subdir3.subdir, True)

    def test_chain_subdirs_and_file(self):
        assets = DotTree('assets')
        assets.mkdir('subdir4').mkdir('subdir').touch('file.txt')
        self.assertTrue(assets.subdir4.subdir.file.txt, True)

    def test_chain_subdirs_and_file_used(self):
        assets = DotTree('assets')
        with open(assets.mkdir('subdir5').mkdir('subdir').touch('file.txt'), 'w') as fh:
            fh.write('chain_test2')
        contents = assets.subdir5.subdir.file.txt.load()
        self.assertEqual(contents, 'chain_test2')

    def test_preload(self):
        assets = DotTree('assets')
        assets.subdir0.preload()
        self.assertEqual(assets.subdir0.file.txt._cached_asset, 'test')

    def test_uncache(self):
        assets = DotTree('assets')
        assets.subdir0.file.txt.load()
        assets.subdir0.file.txt.unload()
        self.assertIsNone(assets.subdir0.file.txt._cached_asset)

    def test_str_path(self):
        assets = DotTree('assets')
        path = str(assets.subdir0.file.txt).split('test')[-1]
        path = '.'.join(path.split(os.path.sep))
        self.assertEqual(path, '.assets.subdir0.file.txt')

    def test_ls(self):
        assets = DotTree('assets')
        contents = assets.subdir0.ls()
        contents.sort()
        self.assertEqual(contents, ['file.txt', 'subterranean/'])

    def test_tree(self):
        assets = DotTree('assets')
        contents = assets.subdir0.subterranean.tree(to_stdout=False)
        output = '''       4 B    *.txt (1)'''
        self.assertEqual(contents, output)

    def test_size(self):
        assets = DotTree('assets')
        contents = assets.subdir0.file.txt.size(to_stdout=False, units='B')
        self.assertEqual(contents, '4 B')

    def test_tree_as_path(self):
        assets = DotTree('assets')
        with open(assets.subdir0.file.txt, 'r') as fh:
            contents = fh.read()
        self.assertEqual(contents, 'test')

    def test_file_not_found_print(self):
        assets = DotTree('assets')
        with self.assertRaises(FileNotFoundError):
            print(assets.subdir0.does_not_exist.txt)

    def test_file_not_found_call(self):
        assets = DotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.subdir0.does_not_exist.txt.load()

    def test_directory_not_found_print(self):
        assets = DotTree('assets')
        with self.assertRaises(FileNotFoundError):
            print(assets.this_dir_does_not_exist)

    def test_directory_not_found_call(self):
        assets = DotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.this_dir_does_not_exist.ls()




class TestGameDotTree(unittest.TestCase):

    def setUp(self):
        cleanup()

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
        contents = assets.subdir0.load()
        self.assertEqual(contents[0], 'test')

    def test_nested_file(self):
        assets = GameDotTree('assets')
        contents = assets.subdir0.file.txt.load()
        self.assertEqual(contents, 'test')

    def test_preload(self):
        assets = GameDotTree('assets')
        assets.subdir0.preload()
        self.assertEqual(assets.subdir0.file.txt._cached_asset, 'test')

    def test_uncache(self):
        assets = GameDotTree('assets')
        assets.subdir0.file.txt.load()
        assets.subdir0.file.txt.unload()
        self.assertIsNone(assets.subdir0.file.txt._cached_asset)

    def test_str_path(self):
        assets = GameDotTree('assets')
        path = str(assets.subdir0.file.txt).split('test')[-1]
        path = '.'.join(path.split(os.path.sep))
        self.assertEqual(path, '.assets.subdir0.file.txt')

    def test_ls(self):
        assets = GameDotTree('assets')
        contents = assets.subdir0.ls()
        contents.sort()
        self.assertEqual(contents, ['file.txt', 'subterranean/'])

    def test_tree(self):
        assets = GameDotTree('assets')
        contents = assets.subdir0.subterranean.tree(to_stdout=False)
        output = '''       4 B    *.txt (1)'''
        self.assertEqual(contents, output)

    def test_size(self):
        assets = GameDotTree('assets')
        contents = assets.subdir0.file.txt.size(to_stdout=False, units='B')
        self.assertEqual(contents, '4 B')

    def test_tree_as_path(self):
        assets = GameDotTree('assets')
        with open(assets.subdir0.file.txt, 'r') as fh:
            contents = fh.read()
        self.assertEqual(contents, 'test')

    def test_file_not_found_print(self):
        assets = GameDotTree('assets')
        with self.assertRaises(FileNotFoundError):
            print(assets.subdir0.does_not_exist.txt)

    def test_file_not_found_call(self):
        assets = GameDotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.subdir0.does_not_exist.txt.load()

    def test_directory_not_found_print(self):
        assets = GameDotTree('assets')
        with self.assertRaises(FileNotFoundError):
            print(assets.this_dir_does_not_exist)

    def test_directory_not_found_call(self):
        assets = GameDotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.this_dir_does_not_exist.ls()

    def test_create_directory_from_trunk(self):
        assets = GameDotTree('assets')
        assets.mkdir('subdir')
        self.assertTrue(os.path.exists(assets.subdir))

    def test_create_directory_from_branch(self):
        assets = GameDotTree('assets')
        assets.subdir0.mkdir('subdir2')
        self.assertTrue(os.path.exists(assets.subdir0.subdir2))

    def test_create_file_from_trunk(self):
        assets = GameDotTree('assets')
        assets.touch('file.txt')
        self.assertTrue(os.path.exists(assets.file.txt))

    def test_create_file_from_branch(self):
        assets = GameDotTree('assets')
        assets.subdir0.touch('file.txt')
        self.assertTrue(os.path.exists(assets.subdir0.file.txt))

    def test_chain_create_subdir_and_file(self):
        assets = GameDotTree('assets')
        with open(assets.mkdir('subdir2').touch('file2.txt'), 'w') as fh:
            fh.write('chain_test')
        contents = assets.subdir2.file2.txt.load()
        self.assertEqual(contents, 'chain_test')

    def test_chain_subdirs(self):
        assets = GameDotTree('assets')
        assets.mkdir('subdir3').mkdir('subdir')
        self.assertTrue(assets.subdir3.subdir, True)

    def test_chain_subdirs_and_file(self):
        assets = GameDotTree('assets')
        assets.mkdir('subdir4').mkdir('subdir').touch('file.txt')
        self.assertTrue(assets.subdir4.subdir.file.txt, True)

    def test_chain_subdirs_and_file_used(self):
        assets = GameDotTree('assets')
        with open(assets.mkdir('subdir5').mkdir('subdir').touch('file.txt'), 'w') as fh:
            fh.write('chain_test2')
        contents = assets.subdir5.subdir.file.txt.load()
        self.assertEqual(contents, 'chain_test2')

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

    def test_rm_trunk_file_from_parent(self):
        assets = GameDotTree('assets')
        assets.touch('file.txt')
        path = str(assets.file.txt)
        assets.rm('file.txt')
        self.assertFalse(os.path.exists(path))

    def test_rm_trunk_file_from_self(self):
        assets = GameDotTree('assets')
        assets.touch('file.txt')
        path = str(assets.file.txt)
        assets.file.txt.rm()
        self.assertFalse(os.path.exists(path))

    def test_rm_node_file_from_parent(self):
        assets = GameDotTree('assets')
        assets.subdir0.touch('file2.txt')
        path = str(assets.subdir0.file2.txt)
        assets.subdir0.rm('file2.txt')
        self.assertFalse(os.path.exists(path))

    def test_rm_node_file_from_self(self):
        assets = GameDotTree('assets')
        assets.subdir0.touch('file3.txt')
        path = str(assets.subdir0.file3.txt)
        assets.subdir0.file3.txt.rm()
        self.assertFalse(os.path.exists(path))

    def test_not_exist_rm_trunk_file_from_parent(self):
        assets = GameDotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.rm('i_do_not_exist.txt')

    def test_not_exist_rm_trunk_file_from_self(self):
        assets = GameDotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.i_do_not_exist.txt.rm()

    def test_not_exist_rm_file_from_self(self):
        assets = GameDotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.subdir0.i_do_not_exist.txt.rm()

    def test_not_exist_rm_file_from_parent(self):
        assets = GameDotTree('assets')
        with self.assertRaises(FileNotFoundError):
            assets.subdir0.rm('i_do_not_exist.txt')

    def test_rm_trunk_dir_from_parent(self):
        assets = GameDotTree('assets')
        assets.mkdir('subdir')
        path = str(assets.subdir)
        assets.rmdir('subdir')
        self.assertFalse(os.path.exists(path))

    def test_rm_trunk_dir_from_self(self):
        assets = GameDotTree('assets')
        assets.mkdir('subdir')
        path = str(assets.subdir)
        assets.subdir.rmdir()
        self.assertFalse(os.path.exists(path))

    def test_rm_node_dir_from_parent(self):
        assets = GameDotTree('assets')
        assets.subdir0.mkdir('subdir')
        path = str(assets.subdir0.subdir)
        assets.subdir0.rmdir('subdir')
        self.assertFalse(os.path.exists(path))

    def test_rm_node_dir_from_self(self):
        assets = GameDotTree('assets')
        assets.subdir0.mkdir('subdir')
        path = str(assets.subdir0.subdir)
        assets.subdir0.subdir.rmdir()
        self.assertFalse(os.path.exists(path))

    def test_fail_rm_trunk_dir_not_empty_from_parent(self):
        assets = GameDotTree('assets')
        with self.assertRaises(DirectoryNotEmptyError):
            assets.rmdir('subdir0')

    def test_fail_rm_trunk_dir_not_empty_from_self(self):
        assets = GameDotTree('assets')
        with self.assertRaises(DirectoryNotEmptyError):
            assets.subdir0.rmdir()

    def test_fail_rm_node_dir_not_empty_from_parent(self):
        assets = GameDotTree('assets')
        with self.assertRaises(DirectoryNotEmptyError):
            assets.subdir0.rmdir('subterranean')

    def test_fail_rm_node_dir_not_empty_from_self(self):
        assets = GameDotTree('assets')
        with self.assertRaises(DirectoryNotEmptyError):
            assets.subdir0.subterranean.rmdir()

    def test_fail_rm_dir_from_trunk(self):
        assets = GameDotTree('assets')
        with self.assertRaises(IsADirectoryError):
            assets.subdir0.rm()
        with self.assertRaises(IsADirectoryError):
            assets.rm('subdir0')

    def test_fail_rmdir_file_from_trunk(self):
        assets = GameDotTree('assets')
        with self.assertRaises(NotADirectoryError):
            assets.test_config.txt.rmdir()
        with self.assertRaises(NotADirectoryError):
            assets.rmdir('test_config.txt')

    def test_fail_rm_dir_from_node(self):
        assets = GameDotTree('assets')
        with self.assertRaises(IsADirectoryError):
            assets.subdir0.subterranean.rm()
        with self.assertRaises(IsADirectoryError):
            assets.subdir0.rm('subterranean')

    def test_fail_rmdir_file_from_node(self):
        assets = GameDotTree('assets')
        with self.assertRaises(NotADirectoryError):
            assets.subdir0.file.txt.rmdir()
        with self.assertRaises(NotADirectoryError):
            assets.subdir0.rmdir('file.txt')

    def test_image_info_from_cache_load(self):
        assets = GameDotTree('assets')
        assets.images.small.png.load()
        output = assets.images.small.png.info(to_stdout=False)
        expected_output = ("{'resolution': (123, 456), 'width': 123, 'height': 456, "
                           "'pixels': 56088, 'aspect': '0.27:1', 'color_bit_depth':"
                           " 32, 'has_alpha': True, 'color_key': None, 'size': "
                           "'242 B'}")
        self.assertEqual(str(output), expected_output)

    def test_image_info_from_preloaded_cache(self):
        assets = GameDotTree('assets')
        assets.images.preload()
        output = assets.images.small.png.info(to_stdout=False)
        expected_output = ("{'resolution': (123, 456), 'width': 123, 'height': 456, "
                           "'pixels': 56088, 'aspect': '0.27:1', 'color_bit_depth':"
                           " 32, 'has_alpha': True, 'color_key': None, 'size': "
                           "'242 B'}")
        self.assertEqual(str(output), expected_output)

    def test_image_info_trunk_from_file(self):
        assets = GameDotTree('assets')
        output = assets.info(assets.images.small.png, to_stdout=False)
        expected_output = ("{'resolution': (123, 456), 'width': 123, 'height': 456, "
                           "'pixels': 56088, 'aspect': '0.27:1', 'color_bit_depth':"
                           " 32, 'has_alpha': True, 'color_key': None, 'size': "
                           "'242 B'}")
        self.assertEqual(str(output), expected_output)

    def test_image_info_node_from_file(self):
        assets = GameDotTree('assets')
        output = assets.images.info(assets.images.small.png, to_stdout=False)
        expected_output = ("{'resolution': (123, 456), 'width': 123, 'height': 456, "
                           "'pixels': 56088, 'aspect': '0.27:1', 'color_bit_depth':"
                           " 32, 'has_alpha': True, 'color_key': None, 'size': "
                           "'242 B'}")
        self.assertEqual(str(output), expected_output)

    def test_image_info_dict_output(self):
        assets = GameDotTree('assets')
        assets.images.small.png.load()
        output = assets.images.small.png.info(to_stdout=False)
        expected_output = ("{'resolution': (123, 456), 'width': 123, 'height': 456, "
                           "'pixels': 56088, 'aspect': '0.27:1', 'color_bit_depth':"
                           " 32, 'has_alpha': True, 'color_key': None, 'size': "
                           "'242 B'}")
        assets.images.small.png.size()
        self.assertEqual(str(output), expected_output)




if __name__ == '__main__':

    unittest.main()

pygame.quit()
