git-rewrite
===========

A helper script for rewriting git history.

Supported fields:

- `AUTHOR_NAME`
- `AUTHOR_EMAIL`
- `AUTHOR_DATE`
- `COMMITTER_NAME`
- `COMMITTER_EMAIL`
- `COMMITTER_DATE`

## Quickstart

The script has two subcommands:

- `git-rewrite dump`
- `git-rewrite apply`

The `dump` step saves the commit data of the current history to a JSON file.

You are supposed to manually edit the file and make any changes you need (e.g. using `sed`).

After you are done, you just `apply` the changes to the repo.

## Installation

### Dependencies

Python 3.7+

There are no 3rd party dependencies.

### just get the script

You can use the script without installing with:

```
wget https://raw.githubusercontent.com/pmav99/git-rewrite/master/git_rewrite/__init__.py
-O git-rewrite
chmod +x git-rewrite
```

### `pipx`

The recommended installation method is [pipx](https://github.com/pipxproject/pipx).  More
specifically, you can install `git-rewrite` for your user with:

```
pipx install --spec https://github.com/pmav99/git-rewrite/archive/master.zip git-rewrite
```

The above command will create a virtual environment in `~/.local/pipx/venvs/git-rewrite`
and add the `git-rewrite` script in `~/.local/bin`.

## How the `dump` works

The `dump` script

1. generates a list of commit hashes since the root commit using:

``` bash
git rev-list --ancestry-path a84477f..HEAD
```

2. parses the commit data of each commit using `git show --format=fuller` and saves them
   to a JSON file.

The end result is something like this:

``` JSON

{
  "root_hash": "a84477f",
  "commits": [
    {
      "commit_hash": "6726ad10be585c21c38726630f7dadf85833f10f",
      "author_name": "John Doe",
      "author_email": "john_doe@gmail.com",
      "author_date": "Thu Jun 6 15:51:30 2019 +0300",
      "committer_name": "john Doe",
      "committer_email": "john_doe@gmail.com",
      "committer_date": "Thu Jun 6 15:53:56 2019 +0300"
    },
    {
      "commit_hash": "4bf077761d21090b46f178b5da534fb9a9da0ca9",
      "author_name": "John Doe",
      "author_email": "john_doe@gmail.com",
      "author_date": "Thu Jun 6 18:12:34 2019 +0300",
      "committer_name": "John Doe",
      "committer_email": "john_doe@gmail.com",
      "committer_date": "Thu Jun 6 18:12:34 2019 +0300"
    }
  ]
}

```

## How the `apply` works

1. the script checkouts the root commit and creates a new branch with a random name.
2. For each commit in the JSON file the script runs:

    1. `git cherry-pick` it in order to bring the changeset into the new branch and change
    the `COMMITTER` data.
    2. `git commit --amend --author <...> --date <...>` in order to update the `AUTHOR`
    data.
