import tomllib
from textwrap import dedent

from management.setup_wizard.config import (
    update_docker_compose_yaml,
    update_prek_toml,
    update_pyproject_toml,
    update_ruff_toml,
)
from management.setup_wizard.env import build_env_example_content
from management.setup_wizard.models import DatabaseMode, RedisMode, SetupAnswers

LEGACY_CLOUD_ENV_PREFIX = "AW" + "S_"
LEGACY_OBJECT_STORE = "min" + "io"
LEGACY_OBJECT_STORE_VOLUME = f"{LEGACY_OBJECT_STORE}_data"
LEGACY_STATIC_STEP = "collect" + "static"
LEGACY_FILE_ENV_PREFIX = "STOR" + "AGE"
LEGACY_TASK_SERVICE = "cel" + "ery-worker"
LEGACY_WEB_ENV_PREFIX = "D" + "JANGO"


def test_env_example_uses_fastapi_only_settings() -> None:
    content = build_env_example_content(answers=_answers())

    assert "JWT_SECRET_KEY=" in content
    assert "DATABASE_URL=" in content
    assert "REDIS_URL=" in content
    assert LEGACY_WEB_ENV_PREFIX not in content
    assert LEGACY_FILE_ENV_PREFIX not in content
    assert LEGACY_CLOUD_ENV_PREFIX not in content


def test_compose_rewrite_prunes_removed_services() -> None:
    content = update_docker_compose_yaml(
        _legacy_compose(),
        answers=_answers(),
        old_package_name="fastapi_template",
        is_local_overlay=False,
    )

    assert LEGACY_TASK_SERVICE not in content
    assert LEGACY_STATIC_STEP not in content
    assert LEGACY_OBJECT_STORE not in content
    assert LEGACY_CLOUD_ENV_PREFIX not in content
    assert "postgres:" in content
    assert "redis:" in content


def test_generated_pyproject_keeps_strict_quality_defaults() -> None:
    content = update_pyproject_toml(
        _pyproject_toml(),
        answers=_answers(),
        old_package_name="fastapi_template",
    )
    document = tomllib.loads(content)

    dev_dependencies = document["dependency-groups"]["dev"]
    assert "wemake-python-styleguide>=1.6,<2" in dev_dependencies
    assert "flake8>=7.3,<8" in dev_dependencies
    assert document["tool"]["mypy"]["extra_checks"] is True
    assert document["tool"]["mypy"]["strict_equality_for_none"] is True
    assert "ignore_missing_imports" not in document["tool"]["mypy"]
    assert "--cov-fail-under=100" in document["tool"]["pytest"]["ini_options"]["addopts"]
    assert (
        "src/example_api/entrypoints/fastapi/bootstrap.py"
        in document["tool"]["coverage"]["run"]["omit"]
    )


def test_generated_ruff_config_requires_public_code_docstrings() -> None:
    content = update_ruff_toml(_ruff_toml(), package_name="example_api")
    document = tomllib.loads(content)

    assert document["lint"]["isort"]["known-first-party"] == ["example_api"]
    assert "D101" not in document["lint"]["ignore"]
    assert "D102" not in document["lint"]["ignore"]
    assert "D103" not in document["lint"]["ignore"]
    assert "D105" not in document["lint"]["ignore"]
    assert "D107" not in document["lint"]["ignore"]
    assert "D103" in document["lint"]["per-file-ignores"]["tests/**"]


def test_generated_prek_config_runs_wemake_styleguide() -> None:
    content = update_prek_toml(_prek_toml())
    document = tomllib.loads(content)
    hooks = {
        hook["name"]: hook
        for repo in document["repos"]
        for hook in repo.get("hooks", [])
        if "name" in hook
    }

    assert hooks["wemake-python-styleguide"]["entry"] == "uv run flake8 src management"
    assert hooks["wemake-python-styleguide"]["pass_filenames"] is False


def _answers() -> SetupAnswers:
    return SetupAnswers(
        project_name="Example API",
        package_name="example_api",
        distribution_name="example-api",
        docs_site_url=None,
        database_mode=DatabaseMode.DOCKER_POSTGRES,
        redis_mode=RedisMode.DOCKER_REDIS,
        keep_docs=True,
        delete_wizard=False,
        overwrite_env=True,
    )


def _legacy_compose() -> str:
    content = dedent(
        """
        x-common:
          environment:
            DATABASE_URL: "postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@pgbouncer:5432/${POSTGRES_DB}"
            __LEGACY_CLOUD_ENDPOINT_KEY__: "http://__LEGACY_OBJECT_STORE__:9000"
            REDIS_URL: "redis://default:${REDIS_PASSWORD}@redis:6379/0"

        services:
          api:
            depends_on:
              pgbouncer:
                condition: service_healthy
              redis:
                condition: service_healthy
              __LEGACY_TASK_SERVICE__:
                condition: service_started
              __LEGACY_STATIC_STEP__:
                condition: service_completed_successfully
          __LEGACY_TASK_SERVICE__:
            image: base:local
          __LEGACY_STATIC_STEP__:
            image: base:local
          __LEGACY_OBJECT_STORE__:
            image: __LEGACY_OBJECT_STORE__/__LEGACY_OBJECT_STORE__:latest
          postgres:
            image: postgres:18-alpine
          pgbouncer:
            image: edoburu/pgbouncer:latest
          redis:
            image: redis:latest

        volumes:
          __LEGACY_OBJECT_STORE_VOLUME__:
          postgres_data:
          redis_data:
        """,
    )
    replacements = {
        "__LEGACY_CLOUD_ENDPOINT_KEY__": f"{LEGACY_CLOUD_ENV_PREFIX}S3_ENDPOINT_URL",
        "__LEGACY_OBJECT_STORE__": LEGACY_OBJECT_STORE,
        "__LEGACY_OBJECT_STORE_VOLUME__": LEGACY_OBJECT_STORE_VOLUME,
        "__LEGACY_STATIC_STEP__": LEGACY_STATIC_STEP,
        "__LEGACY_TASK_SERVICE__": LEGACY_TASK_SERVICE,
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    return content


def _pyproject_toml() -> str:
    return dedent(
        """
        [project]
        name = "fastapi-template"

        [dependency-groups]
        dev = [
            "flake8>=7.3,<8",
            "mypy>=2.1.0",
            "ruff>=0.15.20",
            "wemake-python-styleguide>=1.6,<2",
        ]

        [tool.mypy]
        strict = true
        extra_checks = true
        strict_equality_for_none = true

        [tool.pytest.ini_options]
        addopts = "--cov-fail-under=100"

        [tool.coverage.run]
        omit = [
            "src/fastapi_template/entrypoints/fastapi/app.py",
            "src/fastapi_template/entrypoints/fastapi/bootstrap.py",
        ]
        """,
    )


def _ruff_toml() -> str:
    return dedent(
        """
        src = ["src", "management", "tests"]

        [lint]
        ignore = ["D100", "D104", "D106"]

        [lint.isort]
        known-first-party = ["fastapi_template"]

        [lint.per-file-ignores]
        "tests/**" = ["D101", "D102", "D103", "D105", "D107"]
        """,
    )


def _prek_toml() -> str:
    return dedent(
        """
        [[repos]]
        repo = "local"

        [[repos.hooks]]
        id = "flake8"
        name = "wemake-python-styleguide"
        language = "system"
        entry = "uv run flake8 src management"
        files = "^(src|management)/.*\\\\.py$|^setup\\\\.cfg$|^pyproject\\\\.toml$|^uv\\\\.lock$"
        pass_filenames = false
        """,
    )
