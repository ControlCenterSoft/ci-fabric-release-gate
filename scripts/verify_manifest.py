from __future__ import annotations

import argparse
import json
import re
import subprocess

POLICY = "ci-fabric-privileged-v1"

SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
AUTH_PATH = re.compile(
    r"^authorizations/([0-9a-f]{64})\.json$"
)

MAX_MANIFEST_BYTES = 2048


class VerifyError(RuntimeError):
    pass


def run(*args: str) -> bytes:
    proc = subprocess.run(
        args,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if proc.returncode != 0:
        raise VerifyError(
            f"git command failed: {' '.join(args[:2])}"
        )

    return proc.stdout


def canonical(value: dict) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        + "\n"
    ).encode("ascii")


def parse_manifest(
    data: bytes,
    filename_digest: str,
) -> None:

    if not data or len(data) > MAX_MANIFEST_BYTES:
        raise VerifyError("manifest size invalid")

    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise VerifyError(
            "manifest must be ascii"
        ) from exc

    def unique(pairs):
        out = {}

        for key, value in pairs:
            if key in out:
                raise VerifyError(
                    "duplicate manifest key"
                )

            out[key] = value

        return out

    try:
        value = json.loads(
            text,
            object_pairs_hook=unique,
        )
    except json.JSONDecodeError as exc:
        raise VerifyError(
            "manifest json invalid"
        ) from exc

    expected = {
        "authorization",
        "candidate_digest",
        "evidence_digest",
        "policy",
        "schema",
    }

    if not isinstance(value, dict):
        raise VerifyError(
            "manifest must be object"
        )

    if set(value) != expected:
        raise VerifyError(
            "manifest fields mismatch"
        )

    if (
        value.get("schema") != 1
        or isinstance(value.get("schema"), bool)
    ):
        raise VerifyError("schema invalid")

    if value.get("policy") != POLICY:
        raise VerifyError("policy invalid")

    if value.get("authorization") != "approved":
        raise VerifyError(
            "authorization invalid"
        )

    candidate = value.get("candidate_digest")
    evidence = value.get("evidence_digest")

    if (
        not isinstance(candidate, str)
        or not SHA256.fullmatch(candidate)
    ):
        raise VerifyError(
            "candidate digest invalid"
        )

    if candidate != filename_digest:
        raise VerifyError(
            "candidate digest does not match filename"
        )

    if (
        not isinstance(evidence, str)
        or not SHA256.fullmatch(evidence)
    ):
        raise VerifyError(
            "evidence digest invalid"
        )

    if canonical(value) != data:
        raise VerifyError(
            "manifest is not canonical"
        )


def verify(base: str, head: str) -> None:

    if (
        not SHA1.fullmatch(base)
        or not SHA1.fullmatch(head)
        or base == head
    ):
        raise VerifyError(
            "invalid exact refs"
        )

    actual_head = (
        run("git", "rev-parse", "HEAD")
        .decode()
        .strip()
    )

    if actual_head != head:
        raise VerifyError(
            "checkout head mismatch"
        )

    raw = run(
        "git",
        "diff",
        "--name-status",
        "--no-renames",
        base,
        head,
    ).decode("utf-8")

    lines = [
        line
        for line in raw.splitlines()
        if line
    ]

    if len(lines) != 1:
        raise VerifyError(
            "authorization PR must change exactly one file"
        )

    parts = lines[0].split("\t")

    if len(parts) != 2 or parts[0] != "A":
        raise VerifyError(
            "authorization record must be newly added"
        )

    path = parts[1]

    match = AUTH_PATH.fullmatch(path)

    if not match:
        raise VerifyError(
            "authorization path invalid"
        )

    filename_digest = match.group(1)

    tree = (
        run(
            "git",
            "ls-tree",
            head,
            "--",
            path,
        )
        .decode("utf-8")
        .strip()
    )

    fields = tree.split(None, 3)

    if (
        len(fields) != 4
        or fields[0] != "100644"
        or fields[1] != "blob"
    ):
        raise VerifyError(
            "authorization file mode/type invalid"
        )

    size = int(
        run(
            "git",
            "cat-file",
            "-s",
            f"{head}:{path}",
        )
        .decode()
        .strip()
    )

    if (
        size <= 0
        or size > MAX_MANIFEST_BYTES
    ):
        raise VerifyError(
            "authorization file size invalid"
        )

    data = run(
        "git",
        "show",
        f"{head}:{path}",
    )

    parse_manifest(
        data,
        filename_digest,
    )

    print(
        "CI_FABRIC_PUBLIC_MANIFEST=PASS"
    )
    print(
        "authorization_path=" + path
    )
    print(
        "candidate_digest="
        + filename_digest
    )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--base",
        required=True,
    )
    parser.add_argument(
        "--head",
        required=True,
    )

    args = parser.parse_args()

    verify(
        args.base,
        args.head,
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())

    except VerifyError as exc:
        print(
            "CI_FABRIC_PUBLIC_MANIFEST=BLOCK"
        )
        print(
            "detail=" + str(exc)
        )
        raise SystemExit(78)
