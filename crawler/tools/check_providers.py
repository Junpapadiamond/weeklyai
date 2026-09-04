#!/usr/bin/env python3
"""Check discovery configuration; --live makes one bounded call per required API.

Never logs keys, request headers, or raw provider error bodies.
"""
import argparse
import os
import sys

import requests
from dotenv import load_dotenv


def check_providers(live=False):
    key = os.getenv('PERPLEXITY_API_KEY', '').strip().strip('"').strip("'")
    glm_key = os.getenv('ZHIPU_API_KEY', '').strip().strip('"').strip("'")
    if not key:
        print('ERROR: PERPLEXITY_API_KEY is required for global discovery.')
        return False
    checks = [
        ('Perplexity Search', 'https://api.perplexity.ai/search', key,
         {'query': 'AI product launch', 'max_results': 1}, 'results'),
        ('Perplexity Sonar', 'https://api.perplexity.ai/chat/completions', key,
         {'model': os.getenv('PERPLEXITY_MODEL', 'sonar'), 'messages': [{'role': 'user', 'content': 'Reply OK.'}],
          'max_tokens': 16, 'disable_search': True}, 'choices'),
    ]
    if glm_key and os.getenv('USE_GLM_FOR_CN', 'true').lower() == 'true':
        checks.append(('GLM', 'https://open.bigmodel.cn/api/paas/v4/chat/completions', glm_key,
                       {'model': os.getenv('GLM_MODEL', 'glm-4.7'),
                        'messages': [{'role': 'user', 'content': 'Reply OK.'}], 'max_tokens': 32}, 'choices'))
    else:
        print('China discovery will use Perplexity; ZHIPU_API_KEY is optional.')
    if not live:
        print('Configuration present. Use --live to verify provider access and credits.')
        return True
    success = True
    for name, url, token, payload, field in checks:
        try:
            with requests.post(url, headers={'Authorization': f'Bearer {token}'}, json=payload, timeout=(5, 35)) as response:
                if not response.ok:
                    print(f'ERROR: {name} returned HTTP {response.status_code}; check key, model access and credits.')
                    success = False
                elif not response.json().get(field):
                    print(f'ERROR: {name} returned no usable {field}.')
                    success = False
                else:
                    print(f'OK: {name}')
        except (requests.RequestException, ValueError):
            print(f'ERROR: {name} unavailable or returned invalid JSON.')
            success = False
    return success


if __name__ == '__main__':
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    sys.exit(0 if check_providers(parser.parse_args().live) else 1)
