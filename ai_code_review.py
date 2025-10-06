
import os
import sys
import subprocess
import requests

# --- Configuration ---
# Get CI variables from GitLab
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DIFF_BASE_SHA = os.getenv("CI_MERGE_REQUEST_DIFF_BASE_SHA")

# OpenAI API Configuration
OPENAI_API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o" # Or "gpt-3.5-turbo", "gpt-4-turbo", etc.

# --- Helper Functions ---
def get_git_diff():
    """Executes git diff and returns the output."""
    print("Fetching git diff...")
    command = ["git", "diff", DIFF_BASE_SHA]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error getting git diff:")
        print(result.stderr)
        sys.exit(1)
    return result.stdout

def call_ai_api(diff_content):
    """Sends the diff to the OpenAI API and returns the review."""
    print(f"Sending diff to OpenAI ({OPENAI_MODEL}) for review...")
    
    system_prompt = """Act as a senior software engineer performing a code review. Analyze the following git diff for potential bugs, style issues, security vulnerabilities, and areas for improvement. Provide concise, actionable feedback. Do not comment on trivial things like imports. Format your response in Markdown."""
    user_prompt = f"""Diff:\n\n```diff\n{diff_content}\n```"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    json_data = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    try:
        response = requests.post(OPENAI_API_ENDPOINT, headers=headers, json=json_data, timeout=180)
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
        
        response_json = response.json()
        # Safely access the nested content for OpenAI's format
        choices = response_json.get("choices", [])
        if not choices:
            raise ValueError("No choices found in OpenAI response")
        
        message = choices[0].get("message", {})
        content = message.get("content", "AI response was empty.")
        return content

    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenAI API: {e}")
        print(f"Response body: {response.text if 'response' in locals() else 'No response'}")
        sys.exit(1)
    except (ValueError, KeyError, IndexError) as e:
        print(f"Error parsing OpenAI response: {e}")
        print(f"Full API Response: {response_json}")
        sys.exit(1)

# --- Main Execution ---
if __name__ == "__main__":
    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY", "CI_MERGE_REQUEST_DIFF_BASE_SHA"]
    for var in required_vars:
        if not os.getenv(var):
            print(f"Error: Required environment variable '{var}' is not set.")
            sys.exit(1)

    diff = get_git_diff()
    if not diff:
        print("No changes detected. Skipping AI review.")
        sys.exit(0)

    ai_review = call_ai_api(diff)
    
    # --- Output AI Review to Console ---
    print("\n" + "-"*80)
    print(f"🤖 AI Code Review ({OPENAI_MODEL})")
    print("-"*80)
    print(ai_review)
    print("-"*80 + "\n")
