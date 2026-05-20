import sys
from subprocess import call
import tomli
from pathlib import Path
import os

WIN = os.name == "nt"
LINUX = os.name == "linux"

# https://github.com/conda-forge/linkml-feedstock/pull/6
# as of merging with linkml-runtime, non-linux coverage is unknown (#6)
FAIL_UNDER = os.environ.get("COV_FAIL_UNDER") if LINUX else None

SKIPS = [
    # Expected errors in json schema validation, but none found
    "(test_core_compliance and test_date_types)",
    #  │         # Check that the final type is a self-referential array
    #  │ >       assert anyOf[-1] == {"$ref": f"#/$defs/{array_ref}"}
    #  │ E       AssertionError: assert {'$ref': '#/$defs/AnyShapeArray___T_'} == {'$ref': '#/$defs/AnyShapeArray'}
    #  │ E         Differing items:
    #  │ E         {'$ref': '#/$defs/AnyShapeArray___T_'} != {'$ref': '#/$defs/AnyShapeArray'}
    #  │ E         Full diff:
    #  │ E         - {'$ref': '#/$defs/AnyShapeArray'}
    #  │ E         + {'$ref': '#/$defs/AnyShapeArray___T_'}
    #  │ E         ?                                +++++
    "(test_pydanticgen and test_arrays_anyshape_json_schema)",
]

SKIPS += [
    # https://github.com/conda-forge/linkml-feedstock/pull/6
    #: missing fixture file
    "javagen_with_custom_template",
]

SKIPS += [
    # https://github.com/conda-forge/linkml-feedstock/pull/13
    #: unknown
    #   sqlite3.OperationalError: no such table: responses
    "(test_url_for_format and META and NATIVE_SHEXJ)",
]

if WIN:
    SKIPS += [
        # probably related to fixture line endings?
        "test_issue_179",
        "test_issue_62",
        "test_issue_65",
        "test_metamodel_valid_call",
        "test_models_markdown",
    ]


SRC_DIR = Path(__file__).parent / "src"
PYPROJECT = SRC_DIR / "pyproject.toml"
COVRC_TOML = SRC_DIR / ".coveragerc.toml"
LINKML_PYPROJECT = SRC_DIR / "packages/linkml/pyproject.toml"
PPT_DATA = tomli.loads(LINKML_PYPROJECT.read_text(encoding="utf-8"))
SCRIPTS = sorted(PPT_DATA["project"]["scripts"])
SCRIPT_HELP = [[s, "--help"] for s in SCRIPTS]
COVRC_TOML_CONTENT = """
[run]
source_pkgs = ["linkml", "linkml_runtime"]
"""

TEST = [
    "coverage",
    "run",
    "--source=linkml",
    "--source=linkml_runtime",
    "--branch",
    "-m",
    "pytest",
    "-vv",
    "-n{}".format(os.environ.get("CPU_COUNT", "2")),
    "--tb=long",
    "--color=yes",
    "-k",
    f"""not ({" or ".join(SKIPS)})""",
    # really only useful for local debugging, but...
    "--html=pytest.html",
    "--self-contained-html",
]

REPORT = [
    "coverage",
    "report",
    "--show-missing",
    "--skip-covered",
    *([f"--fail-under={FAIL_UNDER}"] if FAIL_UNDER else []),
]


def do(*args: str):
    print(">>>", *args)
    return call(args)


if __name__ == "__main__":
    COVRC_TOML.write_text(COVRC_TOML_CONTENT, encoding="utf-8")
    for script in [*SCRIPT_HELP, TEST, REPORT]:
        print("\n>>>", *script, "\n", flush=True)
        rc = call(script, cwd=str(SRC_DIR))
        if rc != 0:
            print(f"!!! error {rc} for:", *script)
            sys.exit(rc)
    sys.exit(0)
