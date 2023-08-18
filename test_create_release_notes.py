import unittest
import os
import yaml
from create_release_notes import ReleaseNoteGenerator
import tempfile
import filecmp
import shutil


class TestReleaseNotesGenereator(unittest.TestCase):
    """
    Test cases for ReleaseNoteGenerator. Run using
        python3 -m unittest test_create_release_notes.py
    Tests: 
    1. Release notes are empty file
    2. Release notes are non-empty file
    3. Changelog has different headline format
    """

    def load_data(self, input):
        self.maxDiff = None

        with open("test/" + input + "_input.yaml") as input_file:
            self.input_data = yaml.load(input_file, Loader=yaml.FullLoader)
        for key, value in self.input_data.items():
            os.environ[key] = value
        self.tmpfile = tempfile.NamedTemporaryFile()
        os.environ['GITHUB_OUTPUT'] = self.tmpfile.name

        with open("test/" + input + "_validate.yaml") as validate_file:
            self.validate_data = yaml.load(
                validate_file, Loader=yaml.FullLoader)
        shutil.copyfile(f"test/{input}_release_notes.md",
                        f"test/{input}_release_notes_copy.md")
        self.release_notes_path = f"test/{input}_release_notes_copy.md"
        self.release_notes_validate_path = f"test/{input}_release_notes_validate.md"

    def clean_up(self):
        self.tmpfile.close()
        os.remove(self.release_notes_path)

    def generate_release_note(self):
        self.ReleaseNote = ReleaseNoteGenerator()
        parsed_changelog = self.ReleaseNote.generate()

        self.assertEqual(parsed_changelog, {'release_url': self.input_data['REPO_RELEASE_URL'],
                                            'release_date': self.validate_data['RELEASE_DATE_FORMATTED'],
                                            'release_version': self.input_data['TAG_NAME'],
                                            'repo_name': self.input_data['REPO_NAME'],
                                            'repo_url': self.input_data['REPO_URL'],
                                            'changes': self.validate_data['CHANGES']})
        with open(self.tmpfile.name) as f:
            self.assertEqual(
                f.read(), f"REPO_NAME_RELEASE={self.input_data['REPO_NAME']} {self.input_data['TAG_NAME']}\n")

        self.ReleaseNote.update_release_notes(
            self.release_notes_path, parsed_changelog)
        self.assertEqual(True, filecmp.cmp(self.release_notes_path,
                                           self.release_notes_validate_path))

    def test_generate_release_note(self):
        test_cases = ['empty_file', 'non_empty_file',
                      'different_headline_format']
        for test_case in test_cases:
            with self.subTest(msg=f"input: {test_case}"):
                self.load_data(test_case)
                self.generate_release_note()
                self.clean_up()
