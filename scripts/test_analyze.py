#!/usr/bin/env python3
import argparse
import glob
import os
import sys
from typing import List

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Test the /v1/analyze endpoint with local PDFs.")
    parser.add_argument(
        "--files",
        nargs="*",
        help="Explicit PDF files to send. If omitted, uses all PDFs under tmp/*.pdf",
    )
    parser.add_argument(
        "--instructions",
        required=True,
        help="Instructions to guide the analysis (e.g., 'Summarize and compare benchmarks; output a table.')",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("API_BASE_URL", "http://localhost:8000"),
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--use-files-api",
        action="store_true",
        help="Use Files API upload path (set form field use_files_api=true)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Optional model override (e.g., gemini-2.5-flash)",
    )
    args = parser.parse_args()

    pdf_paths: List[str] = args.files or sorted(glob.glob("tmp/*.pdf"))
    if not pdf_paths:
        print("No PDF files found. Provide --files or place PDFs under tmp/", file=sys.stderr)
        return 1

    # Build multipart form
    open_files = []
    try:
        files = []
        for path in pdf_paths:
            fh = open(path, "rb")
            open_files.append(fh)
            files.append(("files", (os.path.basename(path), fh, "application/pdf")))

        data = {
            "instructions": args.instructions,
            "use_files_api": str(bool(args.use_files_api)).lower(),
        }
        if args.model:
            data["model"] = args.model

        url = args.base_url.rstrip("/") + "/v1/analyze"
        resp = requests.post(url, data=data, files=files, timeout=300)
        print("Status:", resp.status_code)
        try:
            print(resp.json())
        except Exception:
            print(resp.text)
        return 0 if resp.ok else 2
    finally:
        for fh in open_files:
            try:
                fh.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
