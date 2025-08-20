#!/usr/bin/env python3
import argparse
import glob
import json
import os
import sys
from typing import List, Optional

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
        "--use-dropbox-object",
        action="store_true",
        help="Send a Dropbox metadata JSON object in the request body and set use_dropbox=true",
    )
    parser.add_argument(
        "--dropbox-json-file",
        help="Path to a JSON file containing the Dropbox metadata object to send. If omitted and --use-dropbox-object is set, an embedded sample will be used.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Optional model override (e.g., gemini-2.5-flash)",
    )
    args = parser.parse_args()

    # If using Dropbox object mode, send JSON body and query params
    if args.use_dropbox_object:
        # Load JSON payload
        if args.dropbox_json_file:
            try:
                with open(args.dropbox_json_file, "r") as fh:
                    payload = json.load(fh)
            except Exception as exc:
                print(f"Failed to read dropbox JSON file: {exc}", file=sys.stderr)
                return 1
        else:
            # Embedded sample payload (matches the example structure)
            payload = [
                {
                    "data": [
                        {
                            "id": "id:qkC5LfC9xRwAAAAAAAE7fA",
                            "name": "4062-Lincoln Square Apartments - Pre-Design Package - 10-29-2024.pdf",
                            "lastModifiedClient": "2025-01-05T00:55:47Z",
                            "lastModifiedServer": "2025-01-05T00:55:56Z",
                            "rev": "62aeaf97dab148cd4cec3",
                            "contentSize": 23423111,
                            "type": "file",
                            "contentHash": "bfec8009eb58452a4df9e49a9ca5335ff5dc5a077ee5270d3aaa6b8daadfe8a8",
                            "pathLower": "/jensen kaplan/aries shared drive/1 - pre-screen/boyd group ocala deals/4062 lincoln - downtown ocala/4062-lincoln square apartments - pre-design package - 10-29-2024.pdf",
                            "pathDisplay": "/Jensen Kaplan/Aries Shared Drive/1 - Pre-Screen/Boyd Group Ocala Deals/4062 lincoln - downtown ocala/4062-Lincoln Square Apartments - Pre-Design Package - 10-29-2024.pdf",
                            "isDownloadable": True,
                        },
                        {
                            "id": "id:qkC5LfC9xRwAAAAAAAE7fw",
                            "name": "Sale Brochure.pdf",
                            "lastModifiedClient": "2025-01-05T00:57:21Z",
                            "lastModifiedServer": "2025-02-04T07:07:34Z",
                            "rev": "62d4ba9cde6108cd4cec3",
                            "contentSize": 10975733,
                            "type": "file",
                            "contentHash": "5333e1500eac28dac9e486731264aae39440c02d2510d29574fbfcf7fb475df0",
                            "pathLower": "/jensen kaplan/aries shared drive/1 - pre-screen/boyd group ocala deals/mf site (wants to sell it))/sale brochure.pdf",
                            "pathDisplay": "/Jensen Kaplan/Aries Shared Drive/1 - Pre-Screen/Boyd Group Ocala Deals/MF site (wants to sell it))/Sale Brochure.pdf",
                            "isDownloadable": True,
                        },
                    ]
                }
            ]

        params = {
            "use_dropbox": "true",
            "instructions_query": args.instructions,
        }
        # Also extract dropbox_ids from payload when present so the server reliably receives them as query params
        extracted_ids = []
        try:
            for container in payload:
                data = container.get("data") if isinstance(container, dict) else None
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("id"):
                            extracted_ids.append(item["id"])
        except Exception:
            pass
        if extracted_ids:
            params["dropbox_ids"] = ",".join(extracted_ids)
        url = args.base_url.rstrip("/") + "/v1/analyze"
        try:
            resp = requests.post(url, params=params, json=payload, timeout=300)
            print("Status:", resp.status_code)
            try:
                print(resp.json())
            except Exception:
                print(resp.text)
            return 0 if resp.ok else 2
        except Exception as exc:
            print(f"Request failed: {exc}", file=sys.stderr)
            return 1

    # Default: upload local PDFs as before
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
