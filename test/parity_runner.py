#!/usr/bin/env python3
"""
Parity validation: clangd-tidy --export-fixes vs clang-tidy --export-fixes.

For each fixable check in sv_mot's .clang-tidy:
  1. Create a minimal C++ fixture
  2. Run clang-tidy-20 --export-fixes   → baseline YAML
  3. Run clangd-tidy  --stream --export-fixes
  4. Compare: diagnostic count, FileOffset↔stream-line consistency, Replacements presence
  5. Save markdown report to docs/tidy/clangd-parity-YYYY-MM-DD.md

Usage:
    cd /home/briox/Software/tools/clangd-tidy-fix
    python test/parity_runner.py [--report docs/tidy/parity-report.md]
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import yaml

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
# Each entry: check name → (C++ source, clang flags, notes)
# "already_tested" entries were validated by existing pytest fixtures.

ALREADY_TESTED = {"modernize-use-nullptr", "modernize-use-trailing-return-type", "misc-include-cleaner"}

FIXTURES: list[dict] = [
    # -----------------------------------------------------------------------
    # modernize
    # -----------------------------------------------------------------------
    {
        "check": "modernize-avoid-bind",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <functional>
            int add(int x, int y) { return x + y; }
            auto f = std::bind(add, std::placeholders::_1, 2);
        """),
    },
    {
        "check": "modernize-concat-nested-namespaces",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            namespace foo {
            namespace bar {
            void f() {}
            }
            }
        """),
    },
    {
        "check": "modernize-deprecated-headers",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <stdlib.h>
            void f() {}
        """),
    },
    {
        "check": "modernize-loop-convert",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <vector>
            void f() {
                std::vector<int> v = {1, 2, 3};
                for (int i = 0; i < (int)v.size(); ++i) {
                    (void)v[i];
                }
            }
        """),
    },
    {
        "check": "modernize-make-shared",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <memory>
            void f() {
                auto p = std::shared_ptr<int>(new int(5));
            }
        """),
    },
    {
        "check": "modernize-make-unique",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <memory>
            void f() {
                auto p = std::unique_ptr<int>(new int(5));
            }
        """),
    },
    {
        "check": "modernize-pass-by-value",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <string>
            struct Foo {
                std::string s;
                explicit Foo(const std::string& s) : s(s) {}
            };
        """),
    },
    {
        "check": "modernize-redundant-void-arg",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            void f(void);
            void f(void) {}
        """),
    },
    {
        "check": "modernize-replace-random-shuffle",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <algorithm>
            #include <vector>
            void f() {
                std::vector<int> v = {1, 2, 3};
                std::random_shuffle(v.begin(), v.end());
            }
        """),
    },
    {
        "check": "modernize-return-braced-init-list",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            struct Point { int x, y; Point(int a, int b) : x(a), y(b) {} };
            Point origin() { return Point(0, 0); }
        """),
    },
    {
        "check": "modernize-shrink-to-fit",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <vector>
            void f() {
                std::vector<int> v = {1, 2, 3, 4, 5};
                std::vector<int>(v).swap(v);
            }
        """),
    },
    {
        "check": "modernize-type-traits",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <type_traits>
            template<typename T>
            bool f() { return std::is_pointer<T>::value; }
        """),
    },
    {
        "check": "modernize-unary-static-assert",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            static_assert(sizeof(int) == 4, "");
        """),
    },
    {
        "check": "modernize-use-auto",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <vector>
            void f() {
                std::vector<int> v = {1};
                std::vector<int>::iterator it = v.begin();
                (void)it;
            }
        """),
    },
    {
        "check": "modernize-use-bool-literals",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            bool f() { return 0; }
        """),
    },
    {
        "check": "modernize-use-default-member-init",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            struct Foo {
                int x;
                Foo() : x(5) {}
            };
        """),
    },
    {
        "check": "modernize-use-emplace",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <vector>
            #include <utility>
            void f() {
                std::vector<std::pair<int,int>> v;
                v.push_back(std::make_pair(1, 2));
            }
        """),
    },
    {
        "check": "modernize-use-equals-default",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            struct Foo {
                Foo() {}
                ~Foo() {}
            };
        """),
    },
    {
        "check": "modernize-use-equals-delete",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            struct NonCopyable {
            private:
                NonCopyable(const NonCopyable&);
                NonCopyable& operator=(const NonCopyable&);
            };
        """),
    },
    {
        "check": "modernize-use-nodiscard",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            class Resource {
            public:
                bool isEmpty() const { return true; }
                int size() const { return 0; }
            };
        """),
    },
    {
        "check": "modernize-use-noexcept",
        "flags": ["-std=c++11"],
        "cpp": textwrap.dedent("""\
            struct Foo {
                void f() throw() {}
            };
        """),
    },
    {
        "check": "modernize-use-override",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            struct Base {
                virtual void f() {}
                virtual ~Base() {}
            };
            struct Derived : Base {
                virtual void f() {}
            };
        """),
    },
    {
        "check": "modernize-use-starts-ends-with",
        "flags": ["-std=c++20"],
        "cpp": textwrap.dedent("""\
            #include <string>
            bool f(const std::string& s) {
                return s.find("prefix") == 0;
            }
        """),
    },
    {
        "check": "modernize-use-std-numbers",
        "flags": ["-std=c++20"],
        "cpp": textwrap.dedent("""\
            constexpr double kPi = 3.14159265358979323846;
            double area(double r) { return kPi * r * r; }
        """),
    },
    {
        "check": "modernize-use-transparent-functors",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <functional>
            #include <set>
            std::set<int, std::less<int>> s;
        """),
    },
    {
        "check": "modernize-use-uncaught-exceptions",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <exception>
            struct D {
                ~D() {
                    if (std::uncaught_exception()) {}
                }
            };
        """),
    },
    {
        "check": "modernize-use-using",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            typedef int MyInt;
            MyInt f() { return 0; }
        """),
    },
    # -----------------------------------------------------------------------
    # performance
    # -----------------------------------------------------------------------
    {
        "check": "performance-avoid-endl",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <iostream>
            void f() { std::cout << std::endl; }
        """),
    },
    {
        "check": "performance-for-range-copy",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <vector>
            #include <string>
            void f(const std::vector<std::string>& v) {
                for (auto s : v) { (void)s; }
            }
        """),
    },
    {
        "check": "performance-inefficient-vector-operation",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <vector>
            std::vector<int> build() {
                std::vector<int> v;
                for (int i = 0; i < 100; ++i)
                    v.push_back(i);
                return v;
            }
        """),
    },
    {
        "check": "performance-move-const-arg",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <utility>
            #include <string>
            void use(std::string) {}
            void f() {
                const std::string s = "hello";
                use(std::move(s));
            }
        """),
    },
    {
        "check": "performance-unnecessary-copy-initialization",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <string>
            const std::string& get();
            void consume(const std::string&);
            void f() {
                const std::string s = get();
                consume(s);
            }
        """),
    },
    {
        "check": "performance-unnecessary-value-param",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <string>
            void f(const std::string s) { (void)s; }
        """),
    },
    # -----------------------------------------------------------------------
    # readability
    # -----------------------------------------------------------------------
    {
        "check": "readability-container-size-empty",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <vector>
            bool f(const std::vector<int>& v) { return v.size() == 0; }
        """),
    },
    {
        "check": "readability-delete-null-pointer",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            void f(int* p) { if (p) delete p; }
        """),
    },
    {
        "check": "readability-redundant-control-flow",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            void f() { return; }
        """),
    },
    {
        "check": "readability-redundant-member-init",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <string>
            struct Foo {
                std::string s;
                Foo() : s() {}
            };
        """),
    },
    {
        "check": "readability-redundant-smartptr-get",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <memory>
            #include <string>
            std::string f(std::shared_ptr<std::string> p) {
                return *p.get();
            }
        """),
    },
    {
        "check": "readability-redundant-string-cstr",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <string>
            void use(const std::string&);
            void f() {
                std::string s = "hello";
                use(s.c_str());
            }
        """),
    },
    {
        "check": "readability-redundant-string-init",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <string>
            void f() { std::string s = ""; (void)s; }
        """),
    },
    {
        "check": "readability-simplify-boolean-expr",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            bool f(bool x) {
                if (x == true) return true;
                else return false;
            }
        """),
    },
    {
        "check": "readability-string-compare",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <string>
            bool f(const std::string& a, const std::string& b) {
                return a.compare(b) == 0;
            }
        """),
    },
    {
        "check": "readability-uniqueptr-delete-release",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <memory>
            void f() {
                std::unique_ptr<int> p(new int(5));
                delete p.release();
            }
        """),
    },
    {
        "check": "readability-use-std-min-max",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            void clamp(int& x, int lo, int hi) {
                if (x < lo) x = lo;
                if (x > hi) x = hi;
            }
        """),
    },
    {
        "check": "readability-qualified-auto",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <vector>
            void f(std::vector<int*>& v) {
                for (auto x : v) { (void)x; }
            }
        """),
    },
    {
        "check": "readability-const-return-type",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            const int f() { return 0; }
        """),
    },
    # -----------------------------------------------------------------------
    # misc
    # -----------------------------------------------------------------------
    {
        "check": "misc-static-assert",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <cassert>
            void f() { assert(sizeof(int) == 4); }
        """),
    },
    {
        "check": "misc-unused-using-decls",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            #include <vector>
            using std::vector;
            void f() {}
        """),
    },
    {
        "check": "misc-unused-alias-decls",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            namespace myns { struct Foo {}; }
            namespace alias = myns;
            void f() {}
        """),
    },
    # -----------------------------------------------------------------------
    # cppcoreguidelines
    # -----------------------------------------------------------------------
    {
        "check": "cppcoreguidelines-pro-type-cstyle-cast",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            class Base { public: virtual ~Base() = default; };
            class Derived : public Base {};
            void f(Base* b) { Derived* d = (Derived*)b; (void)d; }
        """),
    },
    {
        "check": "cppcoreguidelines-init-variables",
        "flags": ["-std=c++17"],
        "cpp": textwrap.dedent("""\
            void f() {
                int x;
                (void)x;
            }
        """),
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STREAM_RE = re.compile(r"^(.+?):(\d+):\d+:\s+\w+:\s+(.+?)\s*\[([^\]]+)\]\s*$")


def _offset_to_line(filepath: str, offset: int) -> int:
    """Convert byte offset to 1-based line number."""
    try:
        data = pathlib.Path(filepath).read_bytes()
    except OSError:
        return -1
    line = 1
    for byte in data[:offset]:
        if byte == ord("\n"):
            line += 1
    return line


def _make_compile_commands(src: pathlib.Path, flags: list[str]) -> list[dict]:
    return [
        {
            "directory": str(src.parent),
            "file": str(src),
            "command": f"clang++ {' '.join(flags)} -c {src}",
        }
    ]


def _make_clang_tidy_config(check: str) -> str:
    return f"---\nChecks: '-*,{check}'\nWarningsAsErrors: ''\n"


def run_clang_tidy(src: pathlib.Path, work_dir: pathlib.Path) -> dict | None:
    """Run clang-tidy-20 --export-fixes and return parsed YAML or None."""
    out = work_dir / "ct_fixes.yaml"
    cmd = [
        "clang-tidy-20",
        f"-p={work_dir}",
        f"--export-fixes={out}",
        str(src),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=work_dir)
    if not out.exists():
        return None
    try:
        return yaml.safe_load(out.read_text()) or {}
    except yaml.YAMLError:
        return None


def run_clangd_tidy(src: pathlib.Path, work_dir: pathlib.Path) -> tuple[dict | None, str]:
    """Run clangd-tidy --stream --export-fixes. Returns (yaml_dict, stream_text)."""
    out = work_dir / "clangd_fixes.yaml"
    project_root = pathlib.Path(__file__).parent.parent
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root) + os.pathsep + env.get("PYTHONPATH", "")

    cmd = [
        sys.executable, "-m", "clangd_tidy",
        "--clangd-executable", "clangd-20",
        "-p", str(work_dir),
        "--stream",
        "--export-fixes", str(out),
        str(src),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=work_dir)
    stream = r.stdout

    if not out.exists():
        return None, stream
    data = out.read_text()
    if not data.strip():
        return {}, stream
    try:
        return yaml.safe_load(data) or {}, stream
    except yaml.YAMLError:
        return None, stream


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ParityResult:
    check: str
    status: str          # PASS | FAIL | NO_FIX_CLANGD | NO_TRIGGER | ERROR
    ct_diag_count: int = 0
    clangd_diag_count: int = 0
    issues: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core comparison
# ---------------------------------------------------------------------------

def check_parity(fixture: dict, work_dir: pathlib.Path) -> ParityResult:
    check = fixture["check"]
    result = ParityResult(check=check, status="ERROR")

    # Write files
    src = work_dir / "test.cpp"
    src.write_text(fixture["cpp"])
    cc = work_dir / "compile_commands.json"
    cc.write_text(json.dumps(_make_compile_commands(src, fixture["flags"]), indent=2))
    (work_dir / ".clang-tidy").write_text(_make_clang_tidy_config(check))

    # Run clang-tidy
    try:
        ct = run_clang_tidy(src, work_dir)
    except Exception as e:
        result.issues.append(f"clang-tidy error: {e}")
        return result

    ct_diags = (ct or {}).get("Diagnostics", [])
    result.ct_diag_count = len(ct_diags)

    if result.ct_diag_count == 0:
        result.status = "NO_TRIGGER"
        result.notes.append("clang-tidy found no diagnostics — fixture does not trigger the check")
        return result

    # Run clangd-tidy
    try:
        clangd_data, stream = run_clangd_tidy(src, work_dir)
    except Exception as e:
        result.issues.append(f"clangd-tidy error: {e}")
        return result

    clangd_diags = (clangd_data or {}).get("Diagnostics", []) if clangd_data is not None else []
    result.clangd_diag_count = len(clangd_diags)

    # Parse stream output: rule → line
    stream_lines: dict[str, list[int]] = {}
    for line in stream.splitlines():
        m = STREAM_RE.match(line)
        if m:
            rule = m.group(4)
            lineno = int(m.group(2))
            stream_lines.setdefault(rule, []).append(lineno)

    if result.clangd_diag_count == 0:
        # clangd-tidy produced no fixes for this check
        result.status = "NO_FIX_CLANGD"
        if stream_lines:
            result.notes.append(
                f"clangd reported diagnostics in stream ({stream_lines}) but produced no YAML fixes"
            )
        else:
            result.notes.append("clangd produced neither stream diagnostics nor YAML fixes")
        return result

    # Diagnostic count mismatch
    if result.ct_diag_count != result.clangd_diag_count:
        result.issues.append(
            f"diagnostic count mismatch: clang-tidy={result.ct_diag_count}, "
            f"clangd-tidy={result.clangd_diag_count}"
        )

    # Per-diagnostic checks
    for i, diag in enumerate(clangd_diags):
        rule = diag.get("DiagnosticName", "")
        msg = diag.get("DiagnosticMessage", {})
        filepath = msg.get("FilePath", "")
        offset = msg.get("FileOffset", -1)
        repls = msg.get("Replacements", [])

        # FileOffset → line consistency
        if filepath and offset >= 0:
            yaml_line = _offset_to_line(filepath, offset)
            # Find matching stream line for this rule
            expected_lines = stream_lines.get(rule, [])
            if expected_lines:
                if yaml_line not in expected_lines:
                    result.issues.append(
                        f"diag[{i}] {rule}: FileOffset→line={yaml_line} "
                        f"not in stream lines {expected_lines}"
                    )

        # Replacements must be non-empty for checks that have fixes
        if not repls:
            result.issues.append(f"diag[{i}] {rule}: Replacements is empty")

    result.status = "PASS" if not result.issues else "FAIL"
    return result


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

STATUS_EMOJI = {
    "PASS": "✅",
    "FAIL": "❌",
    "NO_FIX_CLANGD": "⚠️",
    "NO_TRIGGER": "🚫",
    "ERROR": "💥",
    "SKIP": "⏭️",
}


def generate_report(results: list[ParityResult]) -> str:
    today = date.today().isoformat()
    lines = [
        f"# clangd-tidy Parity Report — {today}",
        "",
        "Compares `clangd-tidy --export-fixes` YAML format against `clang-tidy-20 --export-fixes`",
        "for each check enabled in sv_mot's `.clang-tidy` that has auto-fixes.",
        "",
        "## Legend",
        "| Status | Meaning |",
        "|--------|---------|",
        "| ✅ PASS | YAML format matches: FileOffset line consistent, Replacements present |",
        "| ❌ FAIL | Mismatch detected — needs fix in replacements.py or main_cli.py |",
        "| ⚠️ NO_FIX_CLANGD | clangd produces no code actions for this check |",
        "| 🚫 NO_TRIGGER | Fixture code doesn't trigger the check — improve fixture |",
        "| 💥 ERROR | Tool crash or unexpected error |",
        "| ⏭️ SKIP | Covered by existing pytest fixture |",
        "",
        "## Summary",
    ]

    counts = {s: 0 for s in STATUS_EMOJI}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1

    for status, emoji in STATUS_EMOJI.items():
        n = counts.get(status, 0)
        if n:
            lines.append(f"- {emoji} {status}: {n}")

    lines += ["", "## Results", ""]
    lines += ["| Check | Status | CT diags | Clangd diags | Issues |",
              "|-------|--------|----------|--------------|--------|"]

    for r in results:
        emoji = STATUS_EMOJI.get(r.status, "?")
        issues_str = "; ".join(r.issues) if r.issues else "-"
        if len(issues_str) > 80:
            issues_str = issues_str[:77] + "..."
        lines.append(
            f"| `{r.check}` | {emoji} {r.status} | {r.ct_diag_count} | {r.clangd_diag_count} | {issues_str} |"
        )

    lines += ["", "## Details", ""]
    for r in results:
        emoji = STATUS_EMOJI.get(r.status, "?")
        lines.append(f"### {emoji} `{r.check}`")
        lines.append(f"**Status:** {r.status} | CT: {r.ct_diag_count} diag(s) | Clangd: {r.clangd_diag_count} diag(s)")
        if r.issues:
            lines.append("")
            lines.append("**Issues:**")
            for issue in r.issues:
                lines.append(f"- {issue}")
        if r.notes:
            lines.append("")
            lines.append("**Notes:**")
            for note in r.notes:
                lines.append(f"- {note}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        default=None,
        help="Path to save markdown report (default: docs/tidy/clangd-parity-YYYY-MM-DD.md)",
    )
    parser.add_argument(
        "--check",
        default=None,
        help="Run only this check (for debugging)",
    )
    args = parser.parse_args()

    # Add already-tested checks as SKIP entries
    results: list[ParityResult] = [
        ParityResult(check=c, status="SKIP", notes=["Covered by existing pytest fixture"])
        for c in sorted(ALREADY_TESTED)
    ]

    fixtures_to_run = [f for f in FIXTURES if f["check"] not in ALREADY_TESTED]
    if args.check:
        fixtures_to_run = [f for f in fixtures_to_run if f["check"] == args.check]

    total = len(fixtures_to_run)
    for i, fixture in enumerate(fixtures_to_run, 1):
        check = fixture["check"]
        print(f"[{i:2d}/{total}] {check} ... ", end="", flush=True)
        with tempfile.TemporaryDirectory(prefix="parity_") as tmpdir:
            result = check_parity(fixture, pathlib.Path(tmpdir))
        emoji = STATUS_EMOJI.get(result.status, "?")
        suffix = ""
        if result.issues:
            suffix = f" ({result.issues[0][:60]})"
        print(f"{emoji} {result.status}{suffix}")
        results.append(result)

    # Sort: FAIL first, then PASS, then rest
    order = {"FAIL": 0, "ERROR": 1, "NO_FIX_CLANGD": 2, "NO_TRIGGER": 3, "PASS": 4, "SKIP": 5}
    results.sort(key=lambda r: (order.get(r.status, 9), r.check))

    # Report path
    report_path = args.report
    if report_path is None:
        today = date.today().isoformat()
        docs_dir = pathlib.Path(__file__).parent.parent / "docs" / "tidy"
        docs_dir.mkdir(parents=True, exist_ok=True)
        report_path = str(docs_dir / f"clangd-parity-{today}.md")

    report = generate_report(results)
    pathlib.Path(report_path).write_text(report)

    # Print summary to stderr
    fail = sum(1 for r in results if r.status == "FAIL")
    no_fix = sum(1 for r in results if r.status == "NO_FIX_CLANGD")
    no_trig = sum(1 for r in results if r.status == "NO_TRIGGER")
    passed = sum(1 for r in results if r.status == "PASS")
    skipped = sum(1 for r in results if r.status == "SKIP")

    print(f"\n{'='*60}")
    print(f"PASS={passed}  FAIL={fail}  NO_FIX={no_fix}  NO_TRIGGER={no_trig}  SKIP={skipped}")
    print(f"Report: {report_path}")

    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
