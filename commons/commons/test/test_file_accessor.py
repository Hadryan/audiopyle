import unittest
from assertpy import assert_that

from commons.file_system import extract_extension, get_file_name


class TestFileAccessor(unittest.TestCase):
    def test_getting_file_name(self):
        assert_that(get_file_name('/etc/passwd')).is_equal_to('passwd')
        assert_that(get_file_name('D:/folder/file.txt')).is_equal_to('file.txt')
        assert_that(get_file_name('D://folder//file.txt')).is_equal_to('file.txt')

    def test_getting_extension(self):
        assert_that(extract_extension('song.ogg')).is_equal_to('ogg')
        assert_that(extract_extension('song.ogg.wav')).is_equal_to('wav')
        assert_that(extract_extension('config')).is_equal_to('')
        assert_that(extract_extension('.vimrc')).is_equal_to('')

    def test_getting_dir_name(self):
        assert_that(get_file_name('/home')).is_equal_to('home')