import os
import json
import logging
import requests


API_BASE = 'https://api.github.com'
ENV = {
    'ACCESS_TOKEN': os.environ.get('ACCESS_TOKEN') or json.load(open(
        'config.json')).get('ACCESS_TOKEN') if os.path.isfile(
            'config.json') else exit(
                '`ACCESS_TOKEN` or `config.json` '
                'file having `ACCESS_TOKEN` is required.'),
    'FILE_TOKENS': os.environ.get('FILE_TOKENS') or json.load(open(
        'config.json')).get('FILE_TOKENS') if os.path.isfile(
            'config.json') else exit(
                '`FILE_TOKENS` or `config.json` '
                'file having `FILE_TOKENS` is required.')
}
HEADERS = {'Authorization': 'token %s' % ENV.get('ACCESS_TOKEN')}


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
logger.addHandler(handler)


def get_file_tokens():

    tokens = ENV.get('FILE_TOKENS', str()).split(',') \
        if ENV.get('FILE_TOKENS') and isinstance(ENV.get(
            'FILE_TOKENS'), str) else ENV.get('FILE_TOKENS', list()) \
        if ENV.get('FILE_TOKENS') else [
            'config.json', 'config.yml', 'config.yaml']

    logger.info('Detected file tokens: %s', ', '.join(tokens))
    return tokens


def search_code(keywords):
    url = API_BASE + '/search/code?q=%s' % (','.join(keywords))
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


def get_latest_commit(repo, owner):

    url = API_BASE + '/repos/{owner}/{repo}/commits/master' \
        .format(owner=owner['login'], repo=repo['name'])

    res = requests.get(url, headers=HEADERS)
    if res.status_code < 400:
        logger.info('  Latest commit is <%s>', res.json().get('sha', str()))
        return res.json().get('sha', str())
    else:
        logger.info('  Could not fetch latest commit: %s', res)
        logger.info('  %s', url)


def search_filenames(code):

    if not(code.get('sha') and code.get('repository') and code[
            'repository'].get('owner')):
        logger.info('<sha>, <repo> or <owner> details are missing: %s',
                    code.get('url', 'Unknown'))
        return

    owner = code.get('repository', dict()).get('owner', dict())
    repo = code.get('repository', dict())

    commit_sha = get_latest_commit(repo, owner)
    if not commit_sha:
        return

    url = API_BASE + '/repos/{owner}/{repo}/git/trees/{sha}?recursive=1' \
        .format(owner=owner['login'], repo=repo['name'], sha=commit_sha)

    res = requests.get(url, headers=HEADERS)
    if res.status_code < 400:
        logger.info('  [%s] files found.', len(res.json().get('tree', list())))
        return [
            x for x in (res.json() or dict()).get('tree', list())
            if x and x.get('type', str()) == 'blob']
    else:
        logger.info('  Unexpected response: %s', res)


def filter_filenames(filenames, tokens):

    logger.info('  Filtering filenames from repos...')

    if not filenames:
        logger.info('    No filenames to filter.')
        logger.info(str())
        return

    for entry in filenames.copy():
        eliminate = True
        if not entry.get('path'):
            continue

        for token in tokens:
            if token in os.path.basename(entry['path']):
                eliminate = False

        if eliminate:
            filenames.remove(entry)

    logger.info('    [%s] files remain after filtering.', len(filenames))
    logger.info(str())


if __name__ == "__main__":
    entries = search_code(['sample'])
    exit(1) if not entries else 0

    tokens = get_file_tokens()
    for entry in entries:
        filenames = search_filenames(entry)
        filter_filenames(filenames, tokens)
