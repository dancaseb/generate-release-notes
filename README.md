# Generate Release notes

Automated generation of release notes for GitHub repositories. Release note is generated from the `CHANGELOG.md` file after a release is published. Then creates a pull request in the documentation repository with the generated release note. 


## Set up

1. Create a `.github/workflows/generate-release-notes.yaml` file with these contents:

    ```yaml
    name: generate-release-notes
    on:
      release:
        types:
          - published

    jobs:
      generate-release-notes:
        runs-on: ubuntu-latest
        steps:
          - uses: indykite/generate-release-notes
            with:
              docs-repo: owner/docs-repo
    ```

2. Merge the above action to your product repository. Make sure you use the [release-please-action](https://github.com/google-github-actions/release-please-action) or similar action to create releases. This action will start generating release notes for the upcoming releases and creating PRs with the release notes in the documentation repository.


## Configuration

| input | description |
|:---:|---|
| `token` | A GitHub secret token, used for checkout and creating PRs. Default `secrets.GITHUB_TOKEN` |
| `docs-repo` | The repository (in format owner/repo) where the release notes will be pushed |
| `base-branch` | The branch where the release notes will be pushed. Default `master` |
| `release-notes-path` | Path to the release notes file. Parent folder must exist. Default `releases/release-notes.md` |
| `allow-automerge` | Allows the action to merge the PRs automatically. Default `false` |


## How generate-release-notes works

After a release is published, the action will generate the release notes from the `CHANGELOG.md` and create a PR in the documentation repository. The PR will contain the generated release note prepended in the `release-notes-path` file. If the file doesn't exist, the action will create the file. If the file is empty the action will write the release note with a page headline. 
