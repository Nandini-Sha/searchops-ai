import json
import os
import uuid
from datetime import datetime, timedelta

def generate_slack_messages():
    messages = [
        {
            "id": str(uuid.uuid4()),
            "channel": "incidents",
            "author": "Alice Smythe",
            "text": "The redis cache is down in us-east-1. Experiencing severe latency on the login endpoint.",
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "channel": "incidents",
            "author": "Bob Smith",
            "text": "Looking into the redis issue. Looks like an OOM kill. I'm scaling up the instance size.",
            "timestamp": (datetime.now() - timedelta(days=2, hours=-1)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "channel": "engineering",
            "author": "Charlie Davis",
            "text": "Does anyone know where the legacy auth code is? The new OAuth migration is breaking.",
            "timestamp": (datetime.now() - timedelta(days=5)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "channel": "engineering",
            "author": "Alice Smythe",
            "text": "It's in the `auth-v1` repo under the `legacy_handlers.py` file. But don't touch it, it's deprecated.",
            "timestamp": (datetime.now() - timedelta(days=5, hours=-2)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "channel": "general",
            "author": "Eve Johnson",
            "text": "Reminder that open enrollment for benefits ends on Friday. Check the HR wiki.",
            "timestamp": (datetime.now() - timedelta(days=1)).isoformat()
        }
    ]
    
    os.makedirs("data/mock", exist_ok=True)
    with open("data/mock/slack_messages.json", "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=4)
    print("Created mock Slack messages.")

def generate_confluence_docs():
    os.makedirs("data/mock/confluence_docs", exist_ok=True)
    
    docs = {
        "incident_response.md": """# Incident Response Playbook
Author: Bob Smith
Last Updated: 2025-10-12

## Process
1. Declare incident in #incidents channel.
2. Identify the severity (SEV-1, SEV-2, SEV-3).
3. If Redis OOM occurs, scale up the instance in AWS console.
4. Draft a post-mortem within 48 hours.
""",
        "hr_benefits.md": """# Employee Benefits
Author: Eve Johnson
Last Updated: 2026-01-05

## Health Insurance
We offer comprehensive health insurance through BlueCross. 
Open enrollment happens every November.

## PTO
Employees get 20 days of paid time off per year.
""",
        "oauth_migration.md": """# OAuth 2.0 Migration Plan
Author: Charlie Davis
Last Updated: 2026-07-20

We are moving away from legacy auth (`auth-v1`).
All new endpoints must use the Auth0 integration.
Do NOT use the old `legacy_handlers.py` logic.
"""
    }
    
    for filename, content in docs.items():
        with open(f"data/mock/confluence_docs/{filename}", "w", encoding="utf-8") as f:
            f.write(content)
    print("Created mock Confluence docs.")

def generate_github_repos():
    os.makedirs("data/mock/github_repos/auth-v1", exist_ok=True)
    os.makedirs("data/mock/github_repos/backend-api", exist_ok=True)
    
    files = {
        "auth-v1/legacy_handlers.py": """
# Deprecated: Do not use for new endpoints
def login(username, password):
    # Old hashing logic
    return check_db(username, password)
""",
        "auth-v1/README.md": """# Auth V1
This repository contains the legacy authentication code. 
It is maintained by Alice Smythe.
Status: Deprecated.
""",
        "backend-api/main.py": """
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}
"""
    }
    
    for filepath, content in files.items():
        with open(f"data/mock/github_repos/{filepath}", "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
    print("Created mock GitHub repos.")

if __name__ == "__main__":
    generate_slack_messages()
    generate_confluence_docs()
    generate_github_repos()
    print("All mock data generated successfully!")
