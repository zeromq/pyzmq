#!/usr/bin/env python3
"""Get the authors of the LGPL-licensed subset of pyzmq (Cython bindings)"""

import re
from collections import defaultdict
from itertools import chain
from os.path import abspath, dirname, join

import git

here = dirname(__file__)
root = dirname(abspath(here))
repo = git.Repo(root)

LAST_CORE_COMMIT = 'db1d4d2f2cdd97955a7db620e667a834920a938a'
PRE_CORE_COMMIT = 'd4e3453b012962fc9bf6ed621019b395f968340c'

EXCLUDED = {
    # docstring only:
    'c2db4af3c591aae99bf437a223d97b30ecbfcd38',
    '7b1ac07a3bbffe70af3adcd663c0cbe6f2a724f7',
    'ce97f46881168c4c05d7885dc48a430c520a9683',
    '14c16a97ffa95bf645ab27bf5b06c3eabda30e5e',
    # accidental swapfile
    '93150feb4a80712c6a379f79d561fbc87405ade8',
}


def get_all_commits():
    return chain(
        repo.iter_commits('master', 'zmq/backend/cython'),
        repo.iter_commits(LAST_CORE_COMMIT, 'zmq/core'),
        repo.iter_commits(PRE_CORE_COMMIT, ['zmq/_zmq.*']),
    )


mailmap = {}
email_names = {}

pat = re.compile(r'\<([^\>]+)\>')
with open(join(root, '.mailmap')) as f:
    for line in f:
        if not line.strip():
            continue
        dest, src = pat.findall(line)
        mailmap[src] = dest
        email_names[dest] = line[: line.index('<')].strip()

author_commits = defaultdict(list)

for commit in get_all_commits():
    # exclude some specific commits (e.g. docstring typos)
    if commit.hexsha in EXCLUDED:
        continue
    # exclude commits that only touch generated pxi files in backend/cython
    backend_cython_files = {
        f for f in commit.stats.files if f.startswith('zmq/backend/cython')
    }
    if backend_cython_files and backend_cython_files.issubset(
        {
            'zmq/backend/cython/constant_enums.pxi',
            'zmq/backend/cython/constants.pxi',
        }
    ):
        continue

    email = commit.author.email
    email = mailmap.get(email, email)
    name = email_names.setdefault(email, commit.author.name)
    author_commits[email].append(commit)


def sort_key(email_commits):
    commits = email_commits[1]
    return (len(commits), commits[0].authored_date)


for email, commits in sorted(author_commits.items(), key=sort_key, reverse=True):
    if len(commits) <= 2:
        msg = '{} ({})'.format(
            ' '.join(c.hexsha[:12] for c in commits),
            commits[0].authored_datetime.year,
        )
    else:
        msg = "{commits} commits ({start}-{end})".format(
            commits=len(commits),
            start=commits[-1].authored_datetime.year,
            end=commits[0].authored_datetime.year,
        )
    print(
        "- [ ] {name} {email}: {msg}".format(
            name=email_names[email],
            email=email,
            msg=msg,
        )
    )
