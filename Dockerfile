FROM ghcr.io/astral-sh/uv:python3.13-trixie

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    PYTHONPATH=/app/src \
    ITEMPOOL_PLUGIN_ROOT=/opt/plugin-venvs \
    PATH="/app/.venv/bin:$PATH"

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --create-home app \
    && mkdir -p /opt/plugins /opt/plugin-venvs \
    && chown app:app /opt/plugins /opt/plugin-venvs

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY --chown=app:app src ./src
COPY --chown=app:app scripts ./scripts
COPY --chown=app:app plugins /opt/plugins

EXPOSE 8000
USER app

ENTRYPOINT ["/app/.venv/bin/python", "/app/scripts/plugin_entrypoint.py"]
CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000", "--entrypoint", "main:app"]
