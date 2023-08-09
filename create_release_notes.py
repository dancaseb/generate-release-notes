import git
import re

class GitRepo:
    def __init__(self) -> None:
       self.repo = git.Repo()
    
    # def update_source_json(self):
    #     tags = self.get_tags()
    #     for commit in self.repo.iter_commits(f"{tags[-2].commit}..{tags[-1].commit}"):
    #         if commit == tags[-1].commit:
    #             continue

    def get_changelog_diff(self):
        diff = self.repo.git.diff("--unified=0", "HEAD^", "HEAD", "--", "CHANGELOG.md")
        if not diff:
            raise Exception("git diff --unified=0 HEAD^ HEAD -- CHANGELOG.md returned empty string. There is nothing to generate the release note from.")
        return diff

class ReleaseNoteGenerator:

    def __init__(self, diff) -> None:
        self.diff = diff

    def parse_diff(self, diff):

        # match lines that start with a + and then a # or *. Plus sign is from the diff
        extract_changes_pattern = r'^\+([#*].*)'
        # match ## or ### followed by a space and then a version number in [] brackets
        version_pattern = r'^#{2,3} (\[([0-9]+\.[0-9]+\.[0-9]+)\].* \(([0-9]{4}-[0-9]{2}-[0-9]{2})\))'
        # extract commit from github url
        commit_pattern = r'https:\/\/.*\/commit\/([0-9a-z]*)'
        # extract date from release url

        changelog_lines = re.findall(extract_changes_pattern, diff, re.M)
        parsed_content = {'release_headline': None, 'release_date': None, 'release_version' : None, 'repository_name': None, 'changes' : []}
        for line in changelog_lines:
            if re.match(version_pattern, line):
                parsed_content['release_headline'] = re.search(version_pattern, line).group(1)
                parsed_content['release_version'] = re.search(version_pattern, line).group(2)
                parsed_content['release_date'] = re.search(version_pattern, line).group(3)
            # e.g., ### Bug Fixes
            elif line.startswith('###'):
                parsed_content['changes'].append({'change_headline': line})
            # commit messages
            elif line.startswith('*'):
                parsed_content['changes'][-1]['change_description'] = line
                parsed_content['changes'][-1]['commit_hash'] = re.search(commit_pattern, line).group(1)
                    
        return parsed_content
    
    def load_file(self, path):
        with open(path, 'r') as file:
            content = file.readlines()
        return content

    def write_file(self, path, content, parsed_diff):
        pattern = r'^\<\!\-\-Release note v[0-9]+\.[0-9]+\.[0-9]+\!\-\-\>$'
        with (open(path, 'w')) as file:
            found_delimiter = False
            for line in content:
                if not found_delimiter and re.match(pattern, line):
                    file.write(f"<!--Release note v{parsed_diff['release_version']}!-->\n")
                    file.write(f"## {parsed_diff['release_headline']}\n\n")
                    for change in parsed_diff['changes']:
                        file.write(f"{change['change_headline']}\n\n")
                        file.write(f"{change['change_description']}\n\n")
                    file.write(line)
                    found_delimiter = True
                else:
                    file.write(line)

    def generate_release_note(self):
        parsed_diff = self.parse_diff(self.diff)
        print(parsed_diff)
        content = self.load_file('release-notes.md')
        self.write_file('release-notes.md', content, parsed_diff)
        
        
    

if __name__ == "__main__":
    Repo = GitRepo()
    changelog_diff = Repo.get_changelog_diff()

    ReleaseNote = ReleaseNoteGenerator(changelog_diff)
    ReleaseNote.generate_release_note()
