"""Generate a local SECRET_KEY in .env after copying the example file."""
from pathlib import Path
import secrets


env_path = Path(__file__).resolve().parent / ".env"
example_path = Path(__file__).resolve().parent / ".env.example"
if not env_path.exists():
    env_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")

lines = env_path.read_text(encoding="utf-8").splitlines()
updated = []
secret_found = False
for line in lines:
    if line.startswith("SECRET_KEY="):
        secret_found = True
        current = line.split("=", 1)[1].strip()
        if not current or current.startswith("replace-with-") or current == "development-only-change-me":
            line = f"SECRET_KEY={secrets.token_urlsafe(48)}"
    updated.append(line)
if not secret_found:
    updated.insert(0, f"SECRET_KEY={secrets.token_urlsafe(48)}")
env_path.write_text("\n".join(updated) + "\n", encoding="utf-8")
print("Local .env is ready. Review APP_BASE_URL and email settings before use.")
