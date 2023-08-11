import git
import re
import argparse
from regex_patterns import extract_changes_pattern, headline_pattern, commit_pattern, delimeter_pattern


class GitRepo:
    def __init__(self, path):
        # path to the git repo
        self.repo = git.Repo(path)

    def get_changelog_diff(self):
        diff = self.repo.git.diff(
            "--unified=0", "HEAD^", "HEAD", "--", "CHANGELOG.md")
        if not diff:
            raise Exception(
                "git diff --unified=0 HEAD^ HEAD -- CHANGELOG.md returned empty string. There is nothing to generate the release note from!")
        return diff


class ReleaseNoteGenerator:

    def _parse_diff(self, diff, source_path):
        source_repo = source_path.split(
            '/')[-2] + '/' + source_path.split('/')[-1]
        parsed_diff = {'compare_changes_url': None, 'release_date': None,
                          'release_version': None, 'source_repo': source_repo, 'source_repo_url': f"https://github.com/{source_repo}", 'changes': []}

        changelog_lines = re.findall(extract_changes_pattern, diff, re.M)
        for line in changelog_lines:
            if re.match(headline_pattern, line):
                parsed_diff['compare_changes_url'] = re.search(
                    headline_pattern, line).group(1)
                parsed_diff['release_version'] = re.search(
                    headline_pattern, line).group(2)
                parsed_diff['release_date'] = re.search(
                    headline_pattern, line).group(3)
            # e.g., ### Bug Fixes
            elif line.startswith('###'):
                parsed_diff['changes'].append({'change_headline': line})
            # commit messages
            elif line.startswith('*'):
                parsed_diff['changes'][-1]['change_description'] = line
                parsed_diff['changes'][-1]['commit_hash'] = re.search(
                    commit_pattern, line).group(1)

        self._verify_parsed_diff(parsed_diff)
        return parsed_diff

    def _load_file(self, path):
        print(path)
        with open(path, 'r') as file:
            content = file.readlines()
        return content

    def _write_file(self, path, file_content, parsed_diff):
        # iterates file content and when finds delimeter_pattern, writes the release note and then continues writing the rest of the file
        with (open(path, 'w')) as file:
            if not file_content:
                # file is empty, write release note at the top
                file.write(f"# Changelog\n\n")
                file.write("***\n")
                self._write_release_notes(file, parsed_diff)
            else:
                found_delimiter = False
                for line in file_content:
                    if not found_delimiter and re.match(delimeter_pattern, line):
                        self._write_release_notes(file, parsed_diff)
                        file.write(line)
                        found_delimiter = True
                    else:
                        file.write(line)

    def _write_release_notes(self, file, parsed_diff):
        file.write(
            f"<!--Release note v{parsed_diff['release_version']}!-->\n")
        file.write(
            f"### {parsed_diff['release_date']} [{parsed_diff['source_repo'].split('/')[-1]}]({parsed_diff['source_repo_url']})\n")
        file.write(f"* #### {parsed_diff['compare_changes_url']}\n\n")
        for change in parsed_diff['changes']:
            file.write(f"{change['change_headline']}\n\n")
            file.write(f"{change['change_description']}\n\n")
        file.write("***\n")

    def _verify_parsed_diff(self, parsed_diff):
        for key, value in parsed_diff.items():
            if value is None:
                raise ValueError(
                    f"Parsing diff failed. All values must be filled in. Value for key {key} is {value}.")

    def generate_release_note(self, changelog_diff, source_repo_path, release_notes_path):
        parsed_diff = self._parse_diff(changelog_diff, source_repo_path)
        print(parsed_diff)
        content = self._load_file(release_notes_path)
        self._write_file(release_notes_path, content, parsed_diff)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate release notes')
    parser.add_argument(
        '--source_repo_path', type=str, help='Source repository path to generate release notes from.', required=True)
    parser.add_argument('--release_notes_path', type=str,
                        help='File name to write release notes to.', required=True)
    args = parser.parse_args()

    Repo = GitRepo(args.source_repo_path)
    changelog_diff = Repo.get_changelog_diff()

    ReleaseNote = ReleaseNoteGenerator()
    ReleaseNote.generate_release_note(
        changelog_diff, args.source_repo_path, args.release_notes_path)
