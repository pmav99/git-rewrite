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

## Commands

The script has two subcommands:

- `git-rewrite dump`
- `git-rewrite apply`

The `dump` step saves the commit data of the current history to a JSON file.

You are supposed to manually edit the file and make any changes you need (e.g. using `sed`).

After you are done, you just `apply` the changes to the repo.

## How the `dump` works

The `dump` script

1. generates a list of commit hashes since the root commit using:

``` bash
git rev-list --ancestry-path a84477f..HEAD
```

2. parses the commit data of each commmit using `git show --format=fuller` and saving
   them to a JSON file. E.g.:

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
      "commit_hash": "5e185576258e52cc24c8e385730de99d31f85fcb",
      "author_name": "John Doe",
      "author_email": "john_doe@gmail.com",
      "author_date": "Thu Jun 6 18:03:37 2019 +0300",
      "committer_name": "John Doe",
      "committer_email": "john_doe@gmail.com",
      "committer_date": "Thu Jun 6 18:03:37 2019 +0300"
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

1. First we checkout the root commit and we create a new branch with a random name
2. For each commit in the JSON file the script runs:
  1. `git cherry-pick` it in order to change the COMMITTER data
  2. `git commit --amend --author <...> --date <...>` in order to change the AUTHOR data
