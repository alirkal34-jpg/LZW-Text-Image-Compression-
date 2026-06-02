# Contributing / Katkı Rehberi

Thank you for considering a contribution.
Katkı yapmayı düşündüğünüz için teşekkür ederiz.

## Development setup / Geliştirme kurulumu

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
pip install pre-commit ruff
pre-commit install
```

## Quality checks / Kalite kontrolleri

```bash
ruff check .
ruff format .
python -m compileall .
```

## Pull Requests
- Keep PRs focused and small.
- Explain motivation and expected impact.
- Reference related issues when applicable.
