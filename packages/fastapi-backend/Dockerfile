FROM python:3.10-slim

WORKDIR /app

# Install OS dependencies (like supervisor) and uv
RUN apt-get update && \
    apt-get install -y supervisor curl && \
    rm -rf /var/lib/apt/lists/* && \
    curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy project configuration and lock file
COPY pyproject.toml uv.lock* ./
# uv.lock* is used to potentially catch platform-specific lock files if they were generated,
# though uv typically uses a single uv.lock.

# Install Python dependencies using uv
# --frozen ensures that the lock file is strictly followed.
# --no-dev skips installation of development dependencies.
# --system-site-packages can be useful if you want uv to be aware of packages already in the base Python image's site-packages,
# but for a clean, isolated build, it's often omitted. We'll omit it for now for a cleaner environment.
RUN uv sync --frozen --no-dev

# Copy the rest of the application code
COPY . .

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/stock_vale_app.conf

EXPOSE 8125

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/stock_vale_app.conf"]
