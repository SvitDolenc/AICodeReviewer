# AICodeReviewer

A small utility and GitLab CI example that runs an AI-powered code review (via OpenAI) on the current merge request diff.

## What this does

- `ai_code_review.py` runs `git diff` against a configured base SHA and sends the diff to the OpenAI Chat API to produce a concise code review.
- The CI job is intended to run in merge-request pipelines (so the script can analyze the MR diff).

## Required environment variables

- `OPENAI_API_KEY` — your OpenAI API key (store this as a masked/protected GitLab CI variable).
- `CI_MERGE_REQUEST_DIFF_BASE_SHA` — provided by GitLab in merge request pipelines; used to compute the diff base.
- GitLab pipeline variables used to control when the job runs (e.g. `CI_PIPELINE_SOURCE`).

## Recommended CI variants

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

## Local testing

To run locally:

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
