"""Deployment artefacts exist and say what the README claims. The image itself is built in CI."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def test_dockerfile_is_multi_stage_non_root_and_secret_free() -> None:
    text = (ROOT / "Dockerfile").read_text()
    assert text.count("FROM ") == 2 and "USER aiapp" in text and "HEALTHCHECK" in text
    assert "uv sync --frozen --no-dev" in text
    assert "API_KEY" not in text and ".env" not in text
    ignored = (ROOT / ".dockerignore").read_text()
    assert ".env" in ignored and "tests" in ignored


def test_prod_compose_wires_dependencies_and_refuses_default_tokens() -> None:
    compose = yaml.safe_load((ROOT / "docker-compose.prod.yml").read_text())
    app = compose["services"]["app"]
    assert set(compose["services"]) == {"app", "postgres", "redis", "phoenix"}
    assert app["environment"]["AIAPP_ENV"] == "production"
    assert "?" in app["environment"]["AIAPP_TOKENS"], "compose fails fast when AIAPP_TOKENS is missing"
    assert app["environment"]["OTEL_EXPORTER_OTLP_ENDPOINT"].startswith("http://phoenix")
    assert "alembic" in app["command"] and set(app["depends_on"]) == {"postgres", "redis"}


def test_ci_runs_the_gates() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    for needle in ("scripts/eval_run.py", "scripts/chaos.py --all", "docker build", "refusing to start in production"):
        assert needle in ci
