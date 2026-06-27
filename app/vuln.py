"""
INTENTIONALLY VULNERABLE — sample target for the security pipeline.

This file exists so the SAST tools in this repo have real code to analyze.
It contains a deliberate CWE-78 command injection used to demonstrate that
CodeQL's data-flow analysis traces untrusted input from source to sink across
function boundaries. See docs/findings/cwe-78-command-injection.md.

Do NOT deploy this. It is a test fixture, not production code.
"""

import subprocess

from flask import Flask, request

app = Flask(__name__)


def run_lookup(hostname):
    # SINK: tainted data is concatenated into a shell command and executed.
    # Because the source is in a different function (lookup, below), a
    # single-line pattern rule does not connect source to sink — CodeQL's
    # cross-function taint tracking does.
    cmd = "nslookup " + hostname
    return subprocess.check_output(cmd, shell=True)  # noqa: S602  (intentional)


@app.route("/lookup")
def lookup():
    host = request.args.get("host")  # SOURCE: user-controlled input
    return run_lookup(host)          # tainted value flows to the sink


def run_lookup_safe(hostname):
    # SAFE counterpart: arguments passed as a list, no shell interpretation.
    return subprocess.check_output(["nslookup", hostname], shell=False)


if __name__ == "__main__":
    app.run()
