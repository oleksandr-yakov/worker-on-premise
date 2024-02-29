import argparse
import requests
import re


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


def main():
    parser = argparse.ArgumentParser(description="Utility for checking tags on GitHub repository")
    parser.add_argument("--check_tag", metavar="TAG", type=str, nargs='?', const='', help="Check if a tag follows the format v#.#.#")
    parser.add_argument("--get_max_tag", action="store_true", help="Find the maximum tag on a GitHub repository")
    parser.add_argument("--repo", metavar="REPO", type=str, help="GitHub repository name in the format 'owner/repo'")
    parser.add_argument("--token", metavar="TOKEN", type=str, help="GitHub personal access token")

    args = parser.parse_args()

    if args.check_tag is not None:
        if not args.check_tag:
            print("Wrong Tag")
            return
        is_valid = check_tag(args.check_tag)
        print(is_valid)
    elif args.get_max_tag:
        if not args.repo or not args.token:
            parser.error("--get_max_tag requires --repo and --token.")
        owner = "oleksandr-yakov/"
        repo_name = owner + args.repo
        max_tag = find_max_tag(repo_name, args.token)
        print(max_tag)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
