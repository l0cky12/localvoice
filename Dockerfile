FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends pipewire-bin wireplumber wl-clipboard libgl1 libegl1 libxkbcommon0 libfontconfig1 && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 localvoice
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/* && rm -rf /wheels
USER localvoice
ENV QT_QPA_PLATFORM=wayland PYTHONUNBUFFERED=1
ENTRYPOINT ["localvoice"]
CMD ["--gui"]
