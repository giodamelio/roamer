"""
Integration tests for roamer
"""

import os
from os.path import expanduser, dirname, realpath
import shutil
import unittest
from tests.session import Session
os.environ["ROAMER_DATA_PATH"] = expanduser(dirname(realpath(__file__)) + '/../tmp/roamer-data/')
from roamer.constant import TEST_DIR, ROAMER_DATA_PATH, TRASH_DIR # pylint: disable=wrong-import-position

HELLO_DIR = os.path.join(TEST_DIR, 'hello/')
DOC_DIR = os.path.join(TEST_DIR, 'docs/')
SPAM_FILE = os.path.join(TEST_DIR, 'spam.txt')
EGG_FILE = os.path.join(TEST_DIR, 'egg.txt')
ARGH_FILE = os.path.join(TEST_DIR, 'argh.md')
RESEARCH_FILE = os.path.join(DOC_DIR, 'research.txt')

def reset_dirs(directories):
    for directory in directories:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)

def build_testing_entries():
    os.makedirs(HELLO_DIR)
    os.makedirs(DOC_DIR)
    with open(SPAM_FILE, "w") as text_file:
        text_file.write('spam file content')
    with open(EGG_FILE, "w") as text_file:
        text_file.write('egg file content')
    with open(ARGH_FILE, "w") as text_file:
        text_file.write('argh file content')
    with open(RESEARCH_FILE, "w") as text_file:
        text_file.write('research file content')


class TestOperations(unittest.TestCase):
    def setUp(self):
        reset_dirs([ROAMER_DATA_PATH, TRASH_DIR, TEST_DIR])
        build_testing_entries()
        self.session = Session(TEST_DIR)

    def test_directory_text_output(self):
        self.assertTrue('hello/' in self.session.text)
        self.assertTrue('docs/' in self.session.text)
        self.assertTrue('spam.txt' in self.session.text)
        self.assertTrue('egg.txt' in self.session.text)
        self.assertTrue('argh.md' in self.session.text)

    def test_create_new_file(self):
        self.session.add_entry('new_file.txt')
        self.session.process()
        path = os.path.join(TEST_DIR, 'new_file.txt')
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.isfile(path))

    def test_create_new_directory(self):
        self.session.add_entry('new_dir/')
        self.session.process()
        path = os.path.join(TEST_DIR, 'new_dir/')
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.isdir(path))

    def test_delete_file(self):
        self.session.remove_entry('argh.md')
        self.session.process()
        self.assertFalse(os.path.exists(ARGH_FILE))

    def test_delete_directory(self):
        self.session.remove_entry('hello/')
        self.session.process()
        self.assertFalse(os.path.exists(HELLO_DIR))

    def test_copy_file(self):
        digest = self.session.get_digest('egg.txt')
        self.session.add_entry('egg2.txt', digest)
        self.session.process()
        path = os.path.join(TEST_DIR, 'egg2.txt')
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as egg2_file:
            self.assertEqual(egg2_file.read(), 'egg file content')

    def test_copy_directory(self):
        digest = self.session.get_digest('docs/')
        self.session.add_entry('docs2/', digest)
        self.session.process()
        path = os.path.join(TEST_DIR, 'docs2/')
        self.assertTrue(os.path.exists(path))
        contents = os.listdir(path)
        self.assertEqual(contents, ['research.txt'])

    def test_rename_file(self):
        self.session.rename('argh.md', 'blarg.md')
        self.session.process()
        self.assertFalse(os.path.exists(ARGH_FILE))
        path = os.path.join(TEST_DIR, 'blarg.md')
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as blarg_file:
            self.assertEqual(blarg_file.read(), 'argh file content')

    def test_rename_directory(self):
        self.session.rename('docs/', 'my-docs/')
        self.session.process()
        self.assertFalse(os.path.exists(DOC_DIR))
        path = os.path.join(TEST_DIR, 'my-docs/')
        self.assertTrue(os.path.exists(path))
        contents = os.listdir(path)
        self.assertEqual(contents, ['research.txt'])

    def test_rename_file_to_directory(self):
        self.session.rename('hello/', 'hello.txt')
        with self.assertRaises(ValueError):
            self.session.process()

    def test_empty_lines(self):
        self.session.text += '\n    \n    \n '
        self.session.process()
        self.assertTrue(os.path.exists(ARGH_FILE))

    def test_multiple_simple_operations(self):
        self.test_create_new_file()
        self.test_delete_directory()
        self.test_rename_file()
        self.test_delete_file()

    def test_copy_file_between_directories(self):
        digest = self.session.get_digest('egg.txt')
        self.session.process()
        second_session = Session(DOC_DIR)
        second_session.add_entry('egg.txt', digest)
        second_session.process()
        path = os.path.join(DOC_DIR, 'egg.txt')
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as egg_file:
            self.assertEqual(egg_file.read(), 'egg file content')

    def test_cut_paste_files_between_directories(self):
        digest = self.session.get_digest('egg.txt')
        self.session.remove_entry('egg.txt')
        self.session.process()
        second_session = Session(DOC_DIR)
        second_session.add_entry('egg.txt', digest)
        second_session.add_entry('egg2.txt', digest)
        second_session.process()
        path = os.path.join(DOC_DIR, 'egg.txt')
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as egg_file:
            self.assertEqual(egg_file.read(), 'egg file content')
        path = os.path.join(DOC_DIR, 'egg2.txt')
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as egg_file:
            self.assertEqual(egg_file.read(), 'egg file content')

    def test_cut_paste_file_same_name(self):
        doc_session = Session(DOC_DIR)
        digest = doc_session.get_digest('research.txt')
        doc_session.remove_entry('research.txt')
        doc_session.process()

        self.session.add_entry('research.txt')
        self.session.process()

        self.session.reload()
        self.session.remove_entry('research.txt')
        self.session.process()

        self.session.reload()
        self.session.add_entry('my_new_research.txt', digest)
        self.session.process()

        path = os.path.join(TEST_DIR, 'my_new_research.txt')
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as research_file:
            self.assertEqual(research_file.read(), 'research file content')

    def test_multiple_file_deletes(self):
        self.session.remove_entry('argh.md')
        self.session.process()
        self.assertFalse(os.path.exists(ARGH_FILE))
        second_session = Session(TEST_DIR)
        second_session.add_entry('argh.md')
        second_session.process()
        self.assertTrue(os.path.exists(ARGH_FILE))
        second_session.reload()
        second_session.remove_entry('argh.md')
        second_session.process()
        self.assertFalse(os.path.exists(ARGH_FILE))

    def test_copy_over_existing_file(self):
        # TODO: mock out sleep
        import time; time.sleep(2)
        erased_spam_digest = self.session.get_digest('spam.txt')
        egg_digest = self.session.get_digest('egg.txt')
        self.session.remove_entry('spam.txt')
        self.session.add_entry('spam.txt', egg_digest)
        self.session.process()
        path = os.path.join(TEST_DIR, 'spam.txt')
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as spam_file:
            self.assertEqual(spam_file.read(), 'egg file content')

        second_session = Session(DOC_DIR)
        second_session.add_entry('spam.txt', erased_spam_digest)
        second_session.process()
        path = os.path.join(DOC_DIR, 'spam.txt')
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as spam_file:
            self.assertEqual(spam_file.read(), 'spam file content')

    def test_copy_file_same_name(self):
        digest = self.session.get_digest('egg.txt')
        for _ in range(3):
            self.session.add_entry('egg.txt', digest)
        self.session.process()
        for egg_file in ['egg.txt', 'egg_copy_1.txt', 'egg_copy_2.txt', 'egg_copy_3.txt']:
            path = os.path.join(TEST_DIR, egg_file)
            self.assertTrue(os.path.exists(path))
            with open(path, 'r') as new_file:
                self.assertEqual(new_file.read(), 'egg file content')

    def test_copy_dir_same_name(self):
        digest = self.session.get_digest('docs/')
        self.session.add_entry('docs/', digest)
        self.session.process()
        for doc_dir in ['docs/', 'docs_copy_1/']:
            path = os.path.join(TEST_DIR, doc_dir)
            self.assertTrue(os.path.exists(path))
            contents = os.listdir(path)
            self.assertEqual(contents, ['research.txt'])

if __name__ == '__main__':
    unittest.main()
