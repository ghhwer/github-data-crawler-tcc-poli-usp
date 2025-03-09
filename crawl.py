# crawl.py
# This script is used to crawl the web and extract relevant data for this study.
# -----------------------------------------------------------------------------
# Usage:
# python crawl.py
# -----------------------------------------------------------------------------
# This script will extract data from the GitHub API for a set of repositories.
import os
import json
import dotenv
import requests
import time
import duckdb
import os
import glob

# Load environment variables from a .env file
dotenv.load_dotenv()

# Load your token securely, e.g., from an environment variable
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEFAULT_SLEEP_TIME_SECONDS = 1

# Set up the headers with your token for authentication
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"token {GITHUB_TOKEN}"
}
# 10 minutes = 600 seconds
def try_request_with_retry(url, headers, retries=5, time_between_retries=600):
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers)
            time.sleep(DEFAULT_SLEEP_TIME_SECONDS)
            if response.status_code == 200:
                return response
            else:
                print("Error:", response.status_code)
                print(response.json())
        except Exception as e:
            print("Error:", e)
        print(f"Retrying in {time_between_retries} seconds...")
        time.sleep(time_between_retries)
        
    print("Failed to get data after retries. URL:", url)
    return None

def get_paginated_until_done(url, project_id, limit=None, base_parse=None):
    done, page, data_accum = False, 1, []
    print("")
    while (not done):
        if limit is not None and page >= limit:
            done = True
            break
        print(f"Paginating over page {page}", end="\r")
        if url.find("?") > -1:
            response = try_request_with_retry(url + f"&page={page}", headers)
        else:
            response = try_request_with_retry(url + f"?page={page}", headers)
        if response.status_code == 200:
            data = response.json()
            if base_parse is not None:
                data = base_parse(data)
            for item in data:
                item['project_id'] = project_id
                item['page'] = page
                data_accum.append(item)
            data_accum += data
            if len(data) == 0:
                done = True
            else:
                page += 1
        else:
            print("Error:", response.status_code)
            print(response.json())
            return None
    print("")
    return data_accum

def get_basic_data(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = try_request_with_retry(url, headers)
    data = response.json()
    data['project_id'] = f"{owner}-{repo}"
    return data

def get_contributors(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    contributors = get_paginated_until_done(url, project_id=f"{owner}-{repo}")
    return contributors

def get_commits(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    commits = get_paginated_until_done(url, project_id=f"{owner}-{repo}")
    return commits

def get_branches(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/branches"
    branches = get_paginated_until_done(url, project_id=f"{owner}-{repo}")
    return branches

def get_releases(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    releases = get_paginated_until_done(url, project_id=f"{owner}-{repo}")
    return releases

def get_issues(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=all"
    issues = get_paginated_until_done(url, project_id=f"{owner}-{repo}")
    return issues

def get_pull_requests(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all"
    pull_requests = get_paginated_until_done(url, project_id=f"{owner}-{repo}")
    return pull_requests

def get_workflows(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows"
    workflows = get_paginated_until_done(url, project_id=f"{owner}-{repo}", base_parse=lambda x: x['workflows'])
    return workflows

def consolidate_duckdb(base_dir):
    print("Consolidating data into a single database...")
    os.remove('database.duck') if os.path.exists('database.duck') else None
    # Create a connection to the database
    con = duckdb.connect(database='database.duck', read_only=False)
    bronze_data = {
        "base": f"{base_dir}/base/*.json",
        "branches": f"{base_dir}/branches/*.json",
        "commits": f"{base_dir}/commits/*.json",
        "contributors": f"{base_dir}/contributors/*.json",
        #"deployments": f"{base_dir}/deployments/*.json",
        "workflows": f"{base_dir}/workflows/*.json",
        "issues": f"{base_dir}/issues/*.json",
        "pull_requests": f"{base_dir}/pull_requests/*.json",
        "releases": f"{base_dir}/releases/*.json"
    }

    # Create a table for each data type
    for table_name, path in bronze_data.items():
        con.execute(f"CREATE TABLE {table_name} AS (SELECT * FROM read_json('{path}', format = 'newline_delimited'))")
    con.close()
    print("Data consolidated successfully!")

def cleanup_non_tracked_projects(base_dir, projects):
    get_filename_linux_or_windows = lambda x: x.split("/")[-1].split(".")[0] if "/" in x else x.split("\\")[-1].split(".")[0]
    # Get all the project ids
    project_ids = [f"{project['owner']}-{project['repo']}" for project in projects]
    # Get all the files in the data directory
    all_files = glob.glob(f"{base_dir}/*/*.json")
    # Get all the project files
    project_files = [file for file in all_files if get_filename_linux_or_windows(file) in project_ids]
    # Get all the non-project files
    non_project_files = [file for file in all_files if file not in project_files]
    # Remove all the non-project files
    for file in non_project_files:
        print(f"Removing non-project file: {file}")
        os.remove(file)
    print("Non-project files removed successfully!")

def extract_data(base_dir, projects):
    # Create directories and store data
    os.makedirs(base_dir, exist_ok=True)
    
    data_functions = {
        "base": get_basic_data,
        "contributors": get_contributors,
        "commits": get_commits,
        "branches": get_branches,
        "releases": get_releases,
        "issues": get_issues,
        "pull_requests": get_pull_requests,
        "workflows": get_workflows
    }
    for project in projects:
        owner, repo = project["owner"], project["repo"]
        print(f"Extracting data for {owner}/{repo}...")
        for key, func in data_functions.items():
            print(f"Extracting data for {key}...")
            os.makedirs(f"{base_dir}/{key}", exist_ok=True)
            exists = os.path.exists(f"{base_dir}/{key}/{owner}-{repo}.json")
            if exists:
                print(f"Data for [{key}] - {owner}/{repo} already exists. Skipping...")
                continue
            
            data = func(owner, repo)
            with open(f"{base_dir}/{key}/{owner}-{repo}.json", "w") as f:
                # if the data is a list then we write it as 1 json object per line
                if isinstance(data, list):
                    for item in data:
                        f.write(json.dumps(item) + "\n")
                else:
                    f.write(json.dumps(data))
        print(f"Data for {owner}/{repo} extracted successfully!")
        
    print("Data extracted successfully!")

def main():
    # Example: Get repository details for a given owner and repo
    projects = [
        {"owner": "facebook", "repo": "react"},
        {"owner": "angular", "repo": "angular"},
        {"owner": "vuejs", "repo": "vue"},
        # Data processing
        {"owner": "apache", "repo": "spark"},
        {"owner": "pandas-dev", "repo": "pandas"},
        {"owner": "duckdb", "repo": "duckdb"},
        # ML
        {"owner": "tensorflow", "repo": "tensorflow"},
        {"owner": "scikit-learn", "repo": "scikit-learn"},
        {"owner": "pytorch", "repo": "pytorch"},
        #{"owner": "microsoft", "repo": "vscode"},
        #{"owner": "atom", "repo": "atom"},
        # Backend
        #{"owner": "fastapi", "repo": "fastapi"},
        {"owner": "pallets", "repo": "flask"},
        #{"owner": "django", "repo": "django"},
        {"owner": "spring-projects", "repo": "spring-framework"},
        {"owner": "go-chi", "repo": "chi"},
        #{"owner": "spring-projects", "repo": "spring-boot"},
    ]
    cleanup_non_tracked_projects("data", projects)
    extract_data("data", projects)
    consolidate_duckdb("data")

if __name__ == "__main__":
    main()