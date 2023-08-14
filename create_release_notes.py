import git
import re
import os
import argparse
from patterns import *


class GitRepo:
    def __init__(self, path):
        # path to the git repo
        self.repo = git.Repo(path)

    def _get_changelog_diff(self):
        diff = self.repo.git.diff(
            "--unified=0", "HEAD^", "HEAD", "--", "CHANGELOG.md")
        if not diff:
            raise Exception(
                "git diff --unified=0 HEAD^ HEAD -- CHANGELOG.md returned empty string. \
                    There is nothing to generate the release note from!")
        return diff

    def _get_repo_url(self):
        return self.repo.git.ls_remote("--get-url")

    def _get_latest_tag(self):
        version = self.repo.git.for_each_ref(
            "--sort=-v:refname", "--format=%(refname:short)", "--count=1", "refs/tags/v*")
        date = self.repo.git.for_each_ref(
            "--sort=-v:refname", "--format=%(authordate:short)", "--count=1", "refs/tags/v*")
        return {'version': version, 'date': date}

    def get_repo_details(self):
        return {'changelog_diff': self._get_changelog_diff(), 'url': self._get_repo_url(),
                'latest_tag': self._get_latest_tag(),
                'name': self.repo.remotes.origin.url.split('/')[-1].removesuffix('.git')}


class ReleaseNoteGenerator:

    def _parse_diff(self, repo):
        parsed_diff = {'compare_changes_url': None, 'release_date': repo['latest_tag']['date'],
                       'release_version': repo['latest_tag']['version'], 'source_repo': repo['name'],
                       'source_repo_url': repo['url'], 'changes': []}

        changelog_lines = re.findall(
            extract_changes_pattern, repo['changelog_diff'], re.M)
        for line in changelog_lines:
            if re.match(version_headline_pattern, line):
                parsed_diff['compare_changes_url'] = re.search(
                    version_headline_pattern, line).group(1)
            # e.g., ### Bug Fixes
            elif line.startswith(change_headline_start):
                parsed_diff['changes'].append(
                    {'change_headline': line.replace(change_headline_start, '', 1)})
                # the changes are grouped under the headline, so we will be modifying the last change headline group
                parsed_diff['changes'][-1]['details'] = []
            # commit messages
            elif line.startswith(commit_message_start):
                commit_message = line.replace(commit_message_start, '', 1)
                commit_hash = re.search(commit_pattern, line).group(1)
                parsed_diff['changes'][-1]['details'].append(
                    {'commit_message': commit_message, 'commit_hash': commit_hash})
        return parsed_diff

    def _load_file(self, path):
        with open(path, 'r') as file:
            content = file.readlines()
        return content

    def _prepend_release_note(self, path, file_content, parsed_diff):
        # iterates file content and when finds delimeter_pattern, writes the release note and then continues writing the rest of the file
        with (open(path, 'w')) as file:
            if not file_content:
                # file is empty, write release note at the top
                self._write_release_note(
                    file, parsed_diff, include_headline=True)
            else:
                found_delimiter = False
                for line in file_content:
                    if not found_delimiter and re.match(delimeter_pattern, line):
                        self._write_release_note(file, parsed_diff)
                        file.write(line)
                        found_delimiter = True
                    else:
                        file.write(line)
                if not found_delimiter:
                    # delimeter_pattern not found in the file and file not empty, append release note
                    self._write_release_note(
                        file, parsed_diff, include_headline=True)

    def _write_release_note(self, file, parsed_diff, include_headline=False):
        if include_headline:
            file.write(f"{file_headline}\n\n")
            file.write(f"{section_delimeter}\n")
        file.write(f"<!--Release note {parsed_diff['release_version']}!-->\n")
        file.write(
            f"### {parsed_diff['release_date']} [{parsed_diff['source_repo']}]({parsed_diff['source_repo_url']})\n")
        file.write(f"* #### {parsed_diff['compare_changes_url']}\n\n")
        for change in parsed_diff['changes']:
            file.write(f"#### {change['change_headline']}\n\n")
            for detail in change['details']:
                file.write(f"* {detail['commit_message']}\n\n")
        file.write(f"{section_delimeter}\n\n")

    def _verify_parsed_diff(self, parsed_diff):
        for key, value in parsed_diff.items():
            if not value:
                raise ValueError(
                    f"Parsing diff failed. All values must be filled in. Value for key '{key}' is missing.")

    def _output_env_variable(self, name, value):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output_file:
            print(f'{name}={value}', file=output_file)

    def generate(self, repo_details, release_notes_path):
        parsed_diff = self._parse_diff(repo_details)
        self._verify_parsed_diff(parsed_diff)
        # output REPO name and RELEASE version as env to be used later in workflow
        self._output_env_variable(
            'REPO_RELEASE', f"{parsed_diff['source_repo']} {parsed_diff['release_version']}")
        file_content = self._load_file(release_notes_path)
        self._prepend_release_note(
            release_notes_path, file_content, parsed_diff)

    def open_env(self):
        print(f"repo url {os.environ['REPO_URL']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate release notes')
    parser.add_argument(
        '--source_repo_path', type=str, help='Source repository path to generate release notes from', required=True)
    parser.add_argument('--release_notes_path', type=str,
                        help='File name to write release notes to', required=True)
    args = parser.parse_args()

    Repo = GitRepo(args.source_repo_path)
    repo_details = Repo.get_repo_details()

    ReleaseNote = ReleaseNoteGenerator()
    ReleaseNote.generate(
        repo_details, args.release_notes_path)
    ReleaseNote.open_env()
