#!/usr/bin/env python3

""" Rewrite git history """

from __future__ import annotations

import argparse
import json
import random
import shlex
import subprocess
import sys

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING

import pydantic

__version__ = "0.2.1"

if TYPE_CHECKING:
    CompletedProcess = subprocess.CompletedProcess[Any]  # pragma: no cover
else:
    CompletedProcess = subprocess.CompletedProcess


def run(cmd: str, **kwargs: Any) -> CompletedProcess:
    defaults: Dict[str, Any] = dict(check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
    defaults.update(kwargs)
    proc = subprocess.run(shlex.split(cmd), **defaults)
    return proc


def get_hashes(root_hash: str) -> List[str]:
    """ Return a list with the commits since `root_hash` """
    cmd = f"git rev-list --ancestry-path {root_hash}..HEAD"
    proc = run(cmd)
    return proc.stdout.splitlines()


def get_commit_data(commit: str) -> List[str]:
    cmd = f"git show --format=fuller {commit}"
    proc = run(cmd)
    return proc.stdout.splitlines()[:5]


def parse_name(git_line: str) -> str:
    """
    Return the author/committer name from git show output

        >>> parse_name('Author:     John Doe <JohnDoe@email.com>')
        'John Doe'

    """
    data = git_line.split(":")[1]
    name = data.split("<")[0].strip()
    return name


def parse_email(git_line: str) -> str:
    """
    Return the author/committer email from git show output

        >>> parse_email('Author:     John Doe <JohnDoe@email.com>')
        'JohnDoe@email.com'

    """
    data = git_line.split(":")[1]
    email = data.split("<")[1].split(">")[0].strip()
    return email


def parse_date(git_line: str) -> str:
    """
    Return the author/committer date from git show output

        >>> parse_date('AuthorDate: Thu Jun 6 14:31:55 2019 +0300')
        'Thu Jun 6 14:31:55 2019 +0300'

    """
    date = git_line.split(":", 1)[1].strip()
    return date


class Commit(pydantic.BaseModel):
    commit_hash: str
    author_name: str
    author_email: str
    author_date: str
    committer_name: str
    committer_email: str
    committer_date: str

    @classmethod
    def from_hash(cls, commit_hash: str) -> Commit:
        """ Return a `Commit` object from a git commit hash """
        commit_data = get_commit_data(commit_hash)
        instance = cls(
            commit_hash=commit_data[0].split()[1].strip(),
            author_name=parse_name(commit_data[1]),
            author_email=parse_email(commit_data[1]),
            author_date=parse_date(commit_data[2]),
            committer_name=parse_name(commit_data[3]),
            committer_email=parse_email(commit_data[3]),
            committer_date=parse_date(commit_data[4]),
        )
        return instance

    def get_env(self) -> Dict[str, str]:
        env = {
            "GIT_AUTHOR_NAME": self.author_name,
            "GIT_AUTHOR_EMAIL": self.author_email,
            "GIT_AUTHOR_DATE": self.author_date,
            "GIT_COMMITTER_NAME": self.committer_name,
            "GIT_COMMITTER_EMAIL": self.committer_email,
            "GIT_COMMITTER_DATE": self.committer_date,
        }
        return env

    def rewrite(self) -> None:
        cmd = f"git cherry-pick {self.commit_hash}"
        run(cmd)
        author = f"{self.author_name} <{self.author_email}>"
        cmd = f"git commit --amend --author '{author}' --date '{self.author_date}' --no-edit"
        run(cmd, env=self.get_env())


class History(pydantic.BaseModel):
    root_hash: str
    commits: List[Commit]

    @classmethod
    def since_hash(cls, root_hash: str) -> History:
        """ Return a `History` object containing `Commit`s since `root_hash` """
        commits=[Commit.from_hash(commit_hash) for commit_hash in get_hashes(root_hash)]
        history = cls(root_hash=root_hash, commits=commits)
        return history

    @classmethod
    def from_file(cls, filename: str = "history.json") -> History:
        with open(filename, "r") as fd:
            data = json.load(fd)

        commits = [Commit(**c) for c in data["commits"]]
        history = cls(root_hash=data["root_hash"], commits=commits)
        return history

    def dump(self, filename: str = "history.json") -> None:
        # XXX should we use "x" here?
        with open(filename, "w") as fd:
            json.dump(self.dict(), fd, indent=2)

    def rewrite(self, branch_name: Optional[str] = None) -> None:
        if branch_name is None:
            branch_name = f"rewrite_{random.randint(1, 9999):04d}"
        cmd = f"git checkout -b {branch_name} {self.root_hash}"
        run(cmd)
        for commit in self.commits:
            commit.rewrite()


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="git-rewrite")
    subparsers = parser.add_subparsers(dest="mode", title="subcommands", help="sub-command help")

    dump = subparsers.add_parser("dump", help="Dump commit data to a JSON file")
    dump.add_argument("root_hash", type=str, help="The hash of the root commit")
    dump.add_argument("-o", "--output", type=str, default="history.json", help="The path of the output file")

    apply = subparsers.add_parser("apply", help="Apply commit data from a JSON file")
    apply.add_argument("-i", "--input", type=str, default="history.json", help="The path of the input file")
    apply.add_argument("-b", "--branch", type=str, default=None, help="The name of the branch that will be created")

    return parser


def dump(args: argparse.Namespace) -> None:
    history = History.since_hash(args.root_hash)
    history.dump(args.output)


def apply(args: argparse.Namespace) -> None:
    history = History.from_file(args.input)
    history.rewrite(branch_name=args.branch)


def cli() -> None:
    parser = get_parser()
    args = parser.parse_args()

    if args.mode == "dump":
        dump(args)
    elif args.mode == "apply":
        apply(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    cli()
