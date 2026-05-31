# Publishing to PyPI

This guide is for maintainers releasing a new version of `lumora-ai`.

## Prerequisites

```bash
pip install --upgrade build twine
```

You need two accounts:
- https://test.pypi.org/  (for dry-runs)
- https://pypi.org/       (for the real release)

Create an **API token** on each (Account settings → API tokens → "Entire account"
or scope it to the `lumora-ai` project after the first upload).

## 1. Bump the version

Edit:
- `pyproject.toml` → `[project] version = "X.Y.Z"`
- `lumora/__init__.py` → `__version__ = "X.Y.Z"`
- `CHANGELOG.md` → add a new section.

Commit the bump:

```bash
git add pyproject.toml lumora/__init__.py CHANGELOG.md
git commit -m "release: vX.Y.Z"
git tag vX.Y.Z
```

## 2. Clean previous builds

```powershell
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
```

```bash
# macOS/Linux
rm -rf dist build *.egg-info
```

## 3. Build sdist and wheel

```bash
python -m build
```

You should see two files in `dist/`:

```
dist/lumora_ai-X.Y.Z-py3-none-any.whl
dist/lumora_ai-X.Y.Z.tar.gz
```

## 4. Validate the artifacts

```bash
python -m twine check dist/*
```

Expect `PASSED` on every file. Then sanity-install the wheel in a throwaway venv:

```powershell
python -m venv .venv_test
.\.venv_test\Scripts\activate
pip install (Get-ChildItem dist\*.whl).FullName
python -c "import lumora; print(lumora.__version__)"
lumora --help
deactivate
Remove-Item -Recurse -Force .venv_test
```

## 5. Upload to TestPyPI (dry run)

```bash
python -m twine upload --repository testpypi dist/*
```

Username: `__token__`
Password: paste your TestPyPI token (starts with `pypi-`).

Test the install:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ lumora-ai
```

## 6. Upload to PyPI (real release)

```bash
python -m twine upload dist/*
```

Username: `__token__`
Password: your PyPI token.

Then verify:

```bash
pip install lumora-ai
python -c "import lumora; print(lumora.__version__)"
```

## 7. Push the tag

```bash
git push origin main --tags
```

## Notes

- Wheels are pure-Python (`py3-none-any`). No C extensions.
- The package name on PyPI is `lumora-ai`; the import name is `lumora`.
- Once a version is uploaded to PyPI it **cannot** be re-uploaded with the same number. Bump even for tiny fixes.
- Consider configuring **PyPI Trusted Publishing** with GitHub Actions to avoid handling long-lived tokens.
