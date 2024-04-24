import os
import sys
import time
from pathlib import Path

import requests

s = requests.Session()
if os.getenv("CIRCLECI_TOKEN"):
    # get credentials
    # not _required_
    s.headers["Circle-Token"] = os.environ["CIRCLECI_TOKEN"]

slug = "gh/zeromq/pyzmq"


def get(url):
    """Make an API request"""
    print(f"Getting {url}")
    r = s.get(url)
    r.raise_for_status()
    return r.json()


def get_pipeline(sha):
    print(f"Getting pipeline for {sha}")
    pipelines = get(f"https://circleci.com/api/v2/project/{slug}/pipeline")
    for pipeline in pipelines["items"]:
        print(
            pipeline['number'], pipeline['vcs']['revision'], pipeline['vcs'].get('tag')
        )
        if pipeline['vcs']['revision'] == sha:
            return pipeline
    print(f"No pipeline found for {sha}")
    return None


def get_workflows(pipeline):
    print(f"Getting workflows for pipeline {pipeline['number']}")
    return get(f"https://circleci.com/api/v2/pipeline/{pipeline['id']}/workflow")[
        "items"
    ]


def get_jobs(workflow):
    print(f"Getting jobs for for workflow {workflow['name']}")
    return get(f"https://circleci.com/api/v2/workflow/{workflow['id']}/job")["items"]


def download_artifact(artifact):
    print(f"Downloading {artifact['path']}")
    p = Path(artifact['path'])
    p.parent.mkdir(exist_ok=True)
    with p.open("wb") as f:
        r = s.get(artifact["url"], stream=True)
        for chunk in r.iter_content(65536):
            f.write(chunk)


def download_artifacts(job):
    print(f"Downloading artifacts for {job['job_number']}")
    for artifact in get(
        f"https://circleci.com/api/v2/project/{slug}/{job['job_number']}/artifacts"
    )["items"]:
        download_artifact(artifact)


def main():
    # circleci tracks the PR head,
    # but github only reports the PR merge commit
    sha = os.getenv("PR_HEAD_SHA")
    if not sha:
        sha = os.environ["GITHUB_SHA"]

    for _ in range(10):
        pipeline = get_pipeline(sha)
        if pipeline is None:
            # wait and try again
            time.sleep(10)
        else:
            break
    workflows = get_workflows(pipeline)
    while not all(w["stopped_at"] for w in workflows):
        for w in workflows:
            print(
                f"Workflow {pipeline['number']}/{w['name']}: {w['status']} started at {w['started_at']}"
            )
        time.sleep(15)
        workflows = get_workflows(pipeline)

    for workflow in workflows:
        if workflow["status"] != "success":
            sys.exit(
                f"workflow {workflow['name']} did not succeed: {workflow['status']}"
            )

    jobs = []
    for workflow in workflows:
        jobs.extend(get_jobs(workflow))
    for job in jobs:
        download_artifacts(job)


if __name__ == "__main__":
    main()
