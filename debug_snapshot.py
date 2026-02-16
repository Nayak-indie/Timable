"""
debug_snapshot.py
------------------

Small helper script to dump the current HTML of a running Streamlit app.

Usage (in a separate terminal, after `streamlit run app.py`):

    conda activate timable
    python debug_snapshot.py http://localhost:8502 > page.html

Then you (and I) can inspect `page.html` for layout issues.
"""

import sys
import time

import requests


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8502"
    # Give the app a moment to start if needed.
    time.sleep(2.0)
    resp = requests.get(url)
    resp.raise_for_status()
    print(resp.text)


if __name__ == "__main__":
    main()

