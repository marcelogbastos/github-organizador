"""Coleta seus repositórios e favoritos do GitHub e gera um dashboard HTML único.

Python 3.10+, sem dependências. Token opcional em GITHUB_TOKEN (inclui repositórios privados).
"""
import argparse
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = 'https://api.github.com'
STAR_FIELDS = ('id', 'full_name', 'description', 'html_url', 'language', 'topics',
               'stargazers_count', 'forks_count', 'pushed_at', 'archived', 'license')
OWN_FIELDS = STAR_FIELDS + ('name', 'fork', 'private', 'visibility', 'created_at', 'updated_at',
                            'size', 'open_issues_count', 'homepage', 'default_branch', 'is_template')


def request(url, token=None, accept='application/vnd.github+json'):
    """GET com tentativas. Retorna (json, tem_próxima_página)."""
    headers = {'Accept': accept, 'User-Agent': 'GitHub-Dashboard', 'X-GitHub-Api-Version': '2022-11-28'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45) as response:
                return json.load(response), 'rel="next"' in response.headers.get('Link', '')
        except urllib.error.HTTPError as exc:
            if exc.code >= 500 and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            if exc.code in (403, 429):
                raise RuntimeError('Limite ou restrição da API. Use GITHUB_TOKEN (ou --gh) e tente novamente. '
                                   'Nenhuma exportação parcial foi gravada.') from None
            raise RuntimeError(f'GitHub retornou HTTP {exc.code}. Confira usuário e token.') from None
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise RuntimeError('Falha de rede após quatro tentativas.') from None
            time.sleep(2 ** attempt)


def paginate(url, token=None, accept='application/vnd.github+json'):
    page = 1
    while True:
        rows, has_next = request(f'{url}{"&" if "?" in url else "?"}per_page=100&page={page}', token, accept)
        yield page, rows
        if not has_next:
            return
        page += 1


def collect_stars(user, token):
    repos = {}
    url = f'{API}/users/{urllib.parse.quote(user)}/starred?sort=created&direction=desc'
    for page, rows in paginate(url, token, 'application/vnd.github.star+json'):
        for item in rows:
            repo = item.get('repo', item)
            repos[repo['id']] = {k: repo.get(k) for k in STAR_FIELDS} | {'starred_at': item.get('starred_at')}
        print(f'Favoritos, página {page}: total {len(repos)}')
    return list(repos.values())


def collect_own(user, token, with_languages=True):
    # Com token, /user/repos inclui os privados; sem token, só os públicos.
    url = f'{API}/user/repos?affiliation=owner&sort=pushed' if token else \
        f'{API}/users/{urllib.parse.quote(user)}/repos?type=owner&sort=pushed'
    repos = {}
    for page, rows in paginate(url, token):
        for repo in rows:
            item = {k: repo.get(k) for k in OWN_FIELDS}
            if item['license']:
                item['license'] = {'spdx_id': item['license'].get('spdx_id'), 'name': item['license'].get('name')}
            repos[repo['id']] = item
        print(f'Repositórios, página {page}: total {len(repos)}')
    if with_languages:
        for number, item in enumerate(repos.values(), 1):
            try:  # falha aqui só deixa o repositório sem detalhamento
                item['languages'] = request(f'{API}/repos/{item["full_name"]}/languages', token)[0]
            except RuntimeError:
                item['languages'] = {}
            if number % 10 == 0:
                print(f'Linguagens: {number}/{len(repos)}')
    return list(repos.values())


def collect_profile(user, token):
    try:
        data = request(f'{API}/users/{urllib.parse.quote(user)}', token)[0]
    except RuntimeError:
        return {}
    return {k: data.get(k) for k in ('login', 'name', 'avatar_url', 'html_url', 'bio',
                                      'followers', 'following', 'public_repos', 'created_at', 'location')}


def render(payload):
    # Impede que descrições de repositórios encerrem a tag script.
    data = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c').replace('&', '\\u0026')
    return (ROOT / 'templates' / 'dashboard.html').read_text(encoding='utf-8').replace('__DATA__', data)


def write_atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(content, encoding='utf-8')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user', default='marcelogbastos')
    parser.add_argument('--output', type=Path, default=ROOT / 'saida', help='Pasta de saída (padrão: saida/)')
    parser.add_argument('--gh', action='store_true', help='Usa o token do GitHub CLI (gh auth token) se GITHUB_TOKEN não existir')
    parser.add_argument('--no-languages', action='store_true', help='Não consulta o detalhamento de linguagens por repositório')
    parser.add_argument('--from-json', type=Path, help='Regenera o HTML a partir de um dados.json, sem acessar a API')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}', args.user):
        parser.error('Usuário inválido')
    token = os.environ.get('GITHUB_TOKEN')
    if not token and args.gh and not args.from_json:
        try:
            token = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, check=True).stdout.strip() or None
        except (OSError, subprocess.CalledProcessError):
            parser.error('Não foi possível obter o token do GitHub CLI')
    try:
        if args.from_json:
            payload = json.loads(args.from_json.read_text(encoding='utf-8'))
        else:
            payload = {'user': args.user, 'generated_at': datetime.now(timezone.utc).isoformat(),
                       'includes_private': bool(token), 'profile': collect_profile(args.user, token),
                       'own': collect_own(args.user, token, not args.no_languages),
                       'stars': collect_stars(args.user, token)}
            write_atomic(args.output / 'dados' / 'dados.json', json.dumps(payload, ensure_ascii=False, indent=2))
        write_atomic(args.output / 'dashboard.html', render(payload))
        print(f'Concluído: {len(payload["own"])} repositórios, {len(payload["stars"])} favoritos -> '
              f'{(args.output / "dashboard.html").resolve()}')
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'Erro: {exc}\n')


if __name__ == '__main__':
    main()
