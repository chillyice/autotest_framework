"""Generate typed Python SDK from OpenAPI spec into api/client/."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "data" / "openapi" / "example.yaml"
OUT_DIR = ROOT / "api"  # openapi-python-client会在其下创建子目录


def main(spec: str | None = None, out: str | None = None):
    spec_path = Path(spec) if spec else SPEC
    out_dir = Path(out) if out else OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-m", "openapi_python_client", "generate",
        "--path", str(spec_path),
        "--output-dir", str(out_dir),
        "--overwrite",
    ]
    subprocess.run(cmd, check=True)
    print(f"[gen-api] SDK generated under {out_dir} from {spec_path}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--spec", help="openapi spec path (default: data/openapi/example.yaml)")
    p.add_argument("--out", help="output dir (default: api/)")
    args = p.parse_args()
    main(spec=args.spec, out=args.out)
