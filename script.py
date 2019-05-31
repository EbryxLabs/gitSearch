import os
import json
import logging
import argparse

import requests
from forestHog import get_args, validate_args, process_repo


HEADERS = dict()
API_BASE = 'https://api.github.com'


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
logger.addHandler(handler)


def update_headers(args):

    global HEADERS
    HEADERS['Authorization'] = 'token ' + args.gtoken


def get_params():

    parser = argparse.ArgumentParser()
    parser.add_argument('--gtoken', default=os.environ.get('ACCESS_TOKEN'),
                        help='Github access token for REST API.')
    parser.add_argument('--conf', default=os.environ.get('CONFIG_FILE'),
                        help='config file for program.')
    parser.add_argument('--search', help='Keyword to search in Github\'s '
                        'all repo code.', action='append')
    parser.add_argument('--json', dest="output_json",
                        action="store_true", help="Output in JSON")
    parser.add_argument("--show-regex", action="store_true",
                        help="prints out regexes that will computed against repo")
    parser.add_argument("--regex", dest="do_regex",
                        action="store_true", help="Enable high signal regex checks")
    parser.add_argument("--rules", dest="rules", default=str(),
                        help="Ignore default regexes and source from json list file")
    parser.add_argument("--add-rules", default=str(),
                        help="Adds more regex rules along with default ones from a json list file")
    parser.add_argument("--entropy", dest="do_entropy",
                        action='store_true', help="Enable entropy checks")
    parser.add_argument("--entropy-wc", type=int, default=20,
                        help="Segments n-length words to check entropy against [default: 20]")
    parser.add_argument("--entropy-b64-thresh", type=float, default=4.5,
                        help="User defined entropy threshold for base64 strings [default: 4.5]")
    parser.add_argument("--entropy-hex-thresh", type=float, default=3,
                        help="User defined entropy threshold for hex strings [default: 3.0]")
    parser.add_argument("--since-commit", dest="since_commit",
                        default=None, help="Only scan from a given commit hash")
    parser.add_argument("--max-depth", dest="max_depth", default=1000000,
                        help="The max commit depth to go back when searching for secrets")
    parser.add_argument("--branch", dest="branch", default=str(),
                        help="Name of the branch to be scanned")
    parser.add_argument("--repo-path", type=str, dest="repo_path", default=str(),
                        help="Path to the cloned repo. If provided, git_url will not be used")
    parser.add_argument("--cleanup", dest="cleanup", action="store_true",
                        help="Clean up all temporary result files")

    args = parser.parse_args()

    if not args.search:
        logger.info('No search keywork provided. Use --search '
                    'param to provide one.')
        exit(1)
    if not args.gtoken:
        logger.info('Github access token not provided. Either specify it '
                    'using --gtoken param or use `ACCESS_TOKEN` env variable.')
        exit(1)
    if not args.conf:
        logger.info('Config file not provided. Either specify it using '
                    '--conf param or use `CONFIG_FILE` env variable.')
        exit(1)
    if not os.path.isfile(args.conf):
        logger.info('Config file not found: %s', args.conf)
        exit(1)

    update_headers(args)
    entropy_options = validate_args(args)
    return (args, entropy_options)


def search_code(keywords):
    url = API_BASE + '/search/code?q=%s' % ('|'.join(keywords))
    logger.info('Searching: %s', url)

    res = requests.get(url, headers=HEADERS)
    if res.status_code < 400:
        repos = [
            x['repository']['name'] for x in res.json().get('items', list())
            if x.get('repository', dict()).get('name')]

        unique_repos = [
            x for x in (res.json() or dict()).get('items', list())
            if x.get('repository', dict()).get('name') not in
            ((repos.remove(x['repository']['name'])
              if x['repository']['name'] in repos else repos) or repos)
        ]

        logger.info('[%s] entries found.', len(unique_repos))
        logger.info(str())
        return unique_repos

    else:
        logger.info('Unexpected response: %s', res)


def run_foresthog(args, options, code):

    url = code.get('repository', dict()).get('html_url', str())
    if not url:
        logger.info('<repository.url> property not found: %s', code.get(
            'repository', dict()).get('full_name'))
        return

    logger.info('Processing repo: %s', url)
    setattr(args, 'git_url', url)
    response = process_repo(args, options, False)
    print(response)


if __name__ == "__main__":

    args, entropy_options = get_params()
    entries = search_code(args.search)
    exit(1) if not entries else 0

    for entry in entries:
        run_foresthog(args, entropy_options, entry)
