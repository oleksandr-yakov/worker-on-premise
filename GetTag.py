import argparse
import requests
import re
import json
OWNER = "oleksandr-yakov/"
WORKER_REPO = "worker-on-premise"


def check_tag(tag):
    pattern = r'^v\d+\.\d+\.\d+$'
    return bool(re.match(pattern, tag))


def find_max_tag(repository_name, token):
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/repos/{repository_name}/tags"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        tags = [tag["name"] for tag in response.json() if tag["name"].startswith("v")]

        def tag_to_tuple(tag):
            return tuple(map(int, re.findall(r'\d+', tag)))

        max_tag = max(tags, key=tag_to_tuple)
        return max_tag

    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
        return None


def create_tag_manifest(worker_tag, core_tag):
    core_version = core_tag.lstrip('v').split('.')
    worker_version = worker_tag.lstrip('v').split('.')

    if len(core_version) != 3 or len(worker_version) != 4:
        print("Invalid tag format")
        return None
    # The first three numbers in the tag from core, the last number from the tag from worker
    manifest_tag = f"v{'.'.join(core_version[:3])}.{worker_version[-1]}"
    return manifest_tag


def get_latest_commit_sha(token):
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/repos/{OWNER}{WORKER_REPO}/commits/main"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        commit_data = response.json()
        commit_sha = commit_data["sha"]
        return commit_sha
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
        return None


def git_tag_worker(token, worker_tag,):

    url = f"https://api.github.com/repos/{OWNER}{WORKER_REPO}/git/refs"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "ref": f"refs/tags/{worker_tag}",
        "sha": get_latest_commit_sha(token)
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        print(f"Tag {worker_tag} created for {WORKER_REPO}")
    else:
        print(f"Failed to create tag for {WORKER_REPO}. Status code: {response.status_code}")
        print(response.text)


def main():
    parser = argparse.ArgumentParser(description="Utility for checking tags on GitHub repository")
    parser.add_argument("--check_tag", metavar="TAG", type=str, nargs='?', const='', help="Check if a tag follows the "
                                                                                          "format v#.#.#")
    parser.add_argument("--get_max_tag", action="store_true", help="Find the maximum tag on a GitHub repository")
    parser.add_argument("--create_tag_worker_by_core", action="store_true", help="Create tag for worker using tag "
                                                                                 "core 4.3.2 and tag worker 4.0.0.7 => "
                                                                                 "4.3.2.7")
    parser.add_argument("--create_tag_worker", action="store_true", help="Create new tag for worker using tag "
                                                                         " max tag core and new tag worker")
    parser.add_argument("--core_repo", metavar="REPO", type=str, help="GitHub Core_*repository name '")
    parser.add_argument("--token", metavar="TOKEN", type=str, help="GitHub personal access token")
    parser.add_argument("--core_tag", metavar="CORE_TAG", type=str, help="Tag from core_*")
    parser.add_argument("--worker_tag", metavar="WORKER_TAG", type=str, help="Tag from worker")

    args = parser.parse_args()

    if args.check_tag is not None:
        if not args.check_tag:
            print("Wrong Core Tag")
            return
        is_valid = check_tag(args.check_tag)
        print(is_valid)
    elif args.get_max_tag:
        if not args.repo or not args.token:
            parser.error("--get_max_tag requires --repo and --token.")
        repo_name = OWNER + args.repo
        max_tag = find_max_tag(repo_name, args.token)
        print(max_tag)
    elif args.create_tag_worker_by_core:
        if not args.token:
            parser.error("--create_tag_worker_by_core requires --core_tag and --token.")
        worker_tag = find_max_tag(OWNER + WORKER_REPO, args.token)
        tag_manifest = create_tag_manifest(worker_tag, args.core_tag)
        git_tag_worker(args.token, tag_manifest)
        print(tag_manifest)
    elif args.create_tag_worker:
        if not args.token:
            parser.error("--create_tag_worker requires --repo --core_tag and --token.")
        core_tag = find_max_tag(OWNER + args.core_repo, args.token)
        manifest_tag = create_tag_manifest(args.worker_tag, core_tag)
        print(manifest_tag)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
