import requests

def get_top_level_directories_only(owner, repo, branch, token=None):
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'token {token}'

    # Step 1: Get the commit SHA for the branch
    branch_url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
    branch_resp = requests.get(branch_url, headers=headers)
    if branch_resp.status_code != 200:
        raise Exception(f"Error fetching branch: {branch_resp.status_code} {branch_resp.text}")
    
    tree_sha = branch_resp.json()['commit']['commit']['tree']['sha']

    # Step 2: Get the full tree recursively
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1"
    tree_resp = requests.get(tree_url, headers=headers)
    if tree_resp.status_code != 200:
        raise Exception(f"Error fetching tree: {tree_resp.status_code} {tree_resp.text}")

    tree_data = tree_resp.json()

    # Step 3: Filter for top-level directories only
    top_level_dirs = set()
    for item in tree_data.get('tree', []):
        if item['type'] == 'tree':
            path_parts = item['path'].split('/')
            if len(path_parts) == 1:
                top_level_dirs.add(path_parts[0])

    return list(top_level_dirs)

# Example usage
dirs = get_top_level_directories_only(
    owner="",
    repo="",
    branch="",
    token="<your_github_token>"  # Optional if public
)

print("Top-level directories only:", dirs)

