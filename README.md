```markdown
# AICodeReviewer

A small utility and GitLab CI example that runs an AI-powered code review (via OpenAI) on the current merge request diff.

This repository includes a tiny script, `ai_code_review.py`, and an example GitLab CI job (`ai_code_review`) that shows how to run it inside your pipeline.

## What this does

- `ai_code_review.py` runs `git diff` against a configured base SHA and sends the diff to the OpenAI Chat API to produce a concise code review.
- The CI job is intended to run in merge-request pipelines (so the script can analyze the MR diff).

## Files

- `ai_code_review.py` — main script that collects a git diff and calls the OpenAI API.
- `requirements.txt` — Python dependencies used by the script (install in the job or locally).

## Required environment variables

- `OPENAI_API_KEY` — your OpenAI API key (store this as a masked/protected GitLab CI variable).
- `CI_MERGE_REQUEST_DIFF_BASE_SHA` — provided by GitLab in merge request pipelines; used to compute the diff base.
- GitLab pipeline variables used to control when the job runs (e.g. `CI_PIPELINE_SOURCE`).

Important: always store `OPENAI_API_KEY` as a masked, protected variable in GitLab CI and avoid printing it to job logs.

## Original job snippet (from .gitlab-ci.yml)

This is the job example you provided (unchanged):

```yaml
ai_code_review:
	stage: review
	image: python:3.10-slim # Use an official Python image
	rules:
		- if: $CI_PIPELINE_SOURCE == 'merge_request_event'
	allow_failure: true
	before_script:
		# Install git and the script's python dependencies
		- apt-get update && apt-get install -y git
		- pip install -r requirements.txt
	script:
		# Execute the script
		- python ai_code_review.py
```

This will work on a typical GitLab runner because the runner checks out the repository automatically. The job installs Git (to make sure git is available for the script), installs Python dependencies and runs the review script.

## Recommended CI variants

Depending on your runner configuration, the repository checkout behavior might be different. Here are two recommended safer variants.

1) Prefer explicit Git strategy (recommended)

Add a `variables` entry to force GitLab to clone/fetch the repository. This is the simplest, most idiomatic approach:

```yaml
ai_code_review:
	stage: review
	image: python:3.10-slim
	variables:
		GIT_STRATEGY: clone
	rules:
		- if: $CI_PIPELINE_SOURCE == 'merge_request_event'
	allow_failure: true
	before_script:
		- apt-get update && apt-get install -y git
		- pip install -r requirements.txt
	script:
		- python ai_code_review.py
```

Why: `GIT_STRATEGY: clone` guarantees the job will obtain a full clone of the repo even if a custom runner or upstream configuration disabled the default checkout.

2) Explicit authenticated clone (when you need to fetch extra refs or the runner does not checkout)

If you must explicitly clone the repository (for example in very minimal images or when `GIT_STRATEGY` can't be used), you can clone using the job token. This example clones the repository into the working directory and ensures the correct commit refs are present:

```yaml
ai_code_review:
	stage: review
	image: python:3.10-slim
	rules:
		- if: $CI_PIPELINE_SOURCE == 'merge_request_event'
	allow_failure: true
	before_script:
		- apt-get update && apt-get install -y git
		- git clone "https://gitlab-ci-token:${CI_JOB_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git" .
		- pip install -r requirements.txt
	script:
		- python ai_code_review.py
```

Notes:
- `${CI_JOB_TOKEN}` is a short-lived token scoped to the current job and is safe for read-only repository access in most setups.
- `${CI_SERVER_HOST}` and `${CI_PROJECT_PATH}` are provided by GitLab; the URL format above yields a repository clone URL that uses the job token for authentication.

## Security & cost considerations

- Protect `OPENAI_API_KEY` in GitLab CI: mark it masked and protected if you only run the job on protected branches.
- Avoid printing sensitive values in the logs. The current script prints errors but does not dump `OPENAI_API_KEY`; keep it that way.
- OpenAI calls may incur cost; rate limit or gate usage in high-traffic projects (for example, only run the job for selected branches or when the MR reaches a certain size).

## Local testing

To run locally (quick smoke test):

1. Create a Python venv and install requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Export your OpenAI key and set a base SHA (example uses HEAD~1 to test):

```bash
export OPENAI_API_KEY="sk_..."
export CI_MERGE_REQUEST_DIFF_BASE_SHA=$(git rev-parse HEAD~1)
python ai_code_review.py
```

If the repo has no differences relative to that base SHA the script will print "No changes detected. Skipping AI review." and exit normally.

## Troubleshooting

- If the job fails with "Error getting git diff": ensure Git is installed and that the configured base SHA (environment variable) exists in the runner's repository. Using `GIT_STRATEGY: clone` or an explicit `git clone` will usually fix missing ref problems.
- If OpenAI calls fail: ensure `OPENAI_API_KEY` is set, the model name in `ai_code_review.py` is valid for your account, and egress traffic to api.openai.com is allowed by your CI network.

## Next steps / improvements

- Add size limits for diffs to avoid sending very large payloads to the OpenAI API (or split by file).
- Store AI reviews as job artifacts or post them to MR comments via the GitLab API.
- Add retries and backoff for API calls and rate-limiting.

---

If you'd like, I can also:
- add a small GitLab job that posts the AI review as an MR comment,
- add a size-check to the Python script, or
- convert the example job to support multiple CI providers.

```
# AICodeReviewer
