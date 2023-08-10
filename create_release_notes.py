import git
import re
import argparse


class GitRepo:
    def __init__(self) -> None:
        self.repo = git.Repo()

    def get_changelog_diff(self):
        diff = self.repo.git.diff(
            "--unified=0", "HEAD^", "HEAD", "--", "CHANGELOG.md")
        if not diff:
            raise Exception(
                "git diff --unified=0 HEAD^ HEAD -- CHANGELOG.md returned empty string. There is nothing to generate the release note from!")
        return diff


class ReleaseNoteGenerator:

    def parse_diff(self, diff, source_repo):

        # match lines that start with a + and then a # or *. Plus sign is from the diff
        extract_changes_pattern = r'^\+([#*].*)'
        # match ## or ### followed by a space and then a version number in [] brackets
        headline_pattern = r'^#{2,3} (\[([0-9]+\.[0-9]+\.[0-9]+)\].*) \(([0-9]{4}-[0-9]{2}-[0-9]{2})\)'
        # extract commit from github url
        commit_pattern = r'https:\/\/.*\/commit\/([0-9a-z]*)'
        # extract date from release url

        changelog_lines = re.findall(extract_changes_pattern, diff, re.M)
        parsed_content = {'compare_changes_url': None, 'release_date': None,
                          'release_version': None, 'source_repo': source_repo, 'source_repo_url': f"https://github.com/{source_repo}", 'changes': []}
        for line in changelog_lines:
            if re.match(headline_pattern, line):
                parsed_content['compare_changes_url'] = re.search(
                    headline_pattern, line).group(1)
                parsed_content['release_version'] = re.search(
                    headline_pattern, line).group(2)
                parsed_content['release_date'] = re.search(
                    headline_pattern, line).group(3)
            # e.g., ### Bug Fixes
            elif line.startswith('###'):
                parsed_content['changes'].append({'change_headline': line})
            # commit messages
            elif line.startswith('*'):
                parsed_content['changes'][-1]['change_description'] = line
                parsed_content['changes'][-1]['commit_hash'] = re.search(
                    commit_pattern, line).group(1)

        return parsed_content

    def load_file(self, path):
        with open(path, 'r') as file:
            content = file.readlines()
        return content

    def write_file(self, path, file_content, parsed_diff):
        # iterates file content and when finds delimeter_pattern, writes the release note and then continues writing the rest of the file
        delimeter_pattern = r'^\<\!\-\-Release note v[0-9]+\.[0-9]+\.[0-9]+\!\-\-\>$'
        with (open(path, 'w')) as file:
            # print(f"content of file is: {file_content}")
            if not file_content:
                # file is empty, write release note at the top
                # print('file is empty, writing release note at the top')
                file.write(f"# Changelog\n\n")
                file.write("***\n")
                self._write_release_notes(file, parsed_diff)
            else:
                # print('appending release note to existing file')
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
            f"### {parsed_diff['release_date']} [{parsed_diff['source_repo'].split('/')[1]}]({parsed_diff['source_repo_url']})\n")
        file.write(f"* #### {parsed_diff['compare_changes_url']}\n\n")
        for change in parsed_diff['changes']:
            file.write(f"{change['change_headline']}\n\n")
            file.write(f"{change['change_description']}\n\n")
        file.write("***\n")

    def generate_release_note(self, changelog_diff, source_repo, filename):
        parsed_diff = self.parse_diff(changelog_diff, source_repo)
        print(parsed_diff)
        content = self.load_file(filename)
        self.write_file(filename, content, parsed_diff)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate release notes')
    parser.add_argument(
        '--source', type=str, help='Source repository to generate release notes from. Owner/repo format', required=True)
    parser.add_argument('--filename', type=str, help='File name to write release notes to. Default is release-notes.md',
                        default='release-notes.md')
    args = parser.parse_args()

    Repo = GitRepo()
    changelog_diff = Repo.get_changelog_diff()

    ReleaseNote = ReleaseNoteGenerator()
    ReleaseNote.generate_release_note(changelog_diff, args.source, args.filename)
