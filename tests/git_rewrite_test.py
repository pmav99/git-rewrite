#!/usr/bin/env python3

import functools
import json
import pathlib
import shlex
import subprocess

import pytest

from git_rewrite import run


JOHN_DOE = "John Doe"
JOHN_DOE_EMAIL = "john_doe@example.com"
JANE_DOE = "Jane Doe"
JANE_DOE_EMAIL = "jane_doe@example.com"


def test_git_rewrite_is_installed() -> None:
    try:
        subprocess.run(shlex.split("git-rewrite --help"))
    except FileNotFoundError:
        pytest.exit("You need to install git-rewrite before running the tests")


# def run(cmd: str, **kwargs) -> subprocess.CompletedProcess:
    # proc = subprocess.run(shlex.split(cmd), check=True, **kwargs)
    # return proc


def get_root_commit(repo_path: pathlib.Path) -> str:
    proc = run("git rev-list --max-parents=0 HEAD", stdout=subprocess.PIPE, universal_newlines=True, cwd=repo_path)
    root_commit = proc.stdout.strip()
    return root_commit


@pytest.fixture
def linear_repo(tmp_path: pathlib.Path) -> pathlib.Path:
    run("git init", cwd=tmp_path)
    run(f"git config user.name '{JOHN_DOE}'", cwd=tmp_path)
    run(f"git config user.email '{JOHN_DOE_EMAIL}'", cwd=tmp_path)
    for filename in ["a", "b", "c", "d", "e", "f", "g"]:
        run(f"touch {filename}", cwd=tmp_path)
        run(f"git add {filename}", cwd=tmp_path)
        run(f"git commit -am 'Adding {filename}'", cwd=tmp_path)
    return tmp_path


def test_idempotency(linear_repo: pathlib.Path) -> None:
    run_repo = functools.partial(run, cwd=linear_repo)
    root_commit = get_root_commit(linear_repo)
    original_history = linear_repo / "original_history.json"
    modified_history = linear_repo / "modified_history.json"
    run_repo(f"git-rewrite dump --output {original_history} {root_commit}")
    run_repo(f"git-rewrite apply --input {original_history}")
    run_repo(f"git-rewrite dump --output {modified_history} {root_commit}")
    commit_pairs = zip(
        json.loads(original_history.read_text())["commits"], json.loads(modified_history.read_text())["commits"]
    )
    for original, modified in commit_pairs:
        print(original)
        assert original["author_name"] == modified["author_name"]
        assert original["author_email"] == modified["author_email"]
        assert original["author_date"] == modified["author_date"]
        assert original["committer_name"] == modified["committer_name"]
        assert original["committer_email"] == modified["committer_email"]
        assert original["committer_date"] == modified["committer_date"]


def test_change_author_and_committer(linear_repo: pathlib.Path) -> None:
    run_repo = functools.partial(run, cwd=linear_repo)
    root_commit = get_root_commit(linear_repo)
    original_history = linear_repo / "original_history.json"
    modified_history = linear_repo / "modified_history.json"
    # dump history
    run_repo(f"git-rewrite dump --output {original_history} {root_commit}")
    original_text = original_history.read_text()
    assert JOHN_DOE in original_text
    assert JOHN_DOE_EMAIL in original_text
    assert JANE_DOE not in original_text
    assert JANE_DOE_EMAIL not in original_text
    # Edit the JSON file containing the history
    run_repo(f"sed {original_history} -i -e 's/{JOHN_DOE}/{JANE_DOE}/g'")
    run_repo(f"sed {original_history} -i -e 's/{JOHN_DOE_EMAIL}/{JANE_DOE_EMAIL}/g'")
    # Apply the history and re-dump
    run_repo(f"git-rewrite apply --input {original_history}")
    run_repo(f"git-rewrite dump --output {modified_history} {root_commit}")
    modified_text = modified_history.read_text()
    assert JOHN_DOE not in modified_text
    assert JOHN_DOE_EMAIL not in modified_text
    assert JANE_DOE in modified_text
    assert JANE_DOE_EMAIL in modified_text
