"""Production entrypoint: python tools/start_production.py. Fails closed."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from backend.env_loader import load_project_env
    from tools.deploy_preflight import check
    load_project_env()
    problems = check()
    if problems:
        for problem in problems:
            print('FAIL:', problem)
        return 1
    import os
    import uvicorn
    uvicorn.run('backend.main:app', host=os.getenv('HOST', '127.0.0.1'),
                port=int(os.getenv('PORT', '8000')),
                proxy_headers=True, forwarded_allow_ips=os.environ['FORWARDED_ALLOW_IPS'],
                access_log=False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
