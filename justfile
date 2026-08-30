set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

repo_dir := justfile_directory()
forum_image := "sirbigg/am-forum:latest"
docker_platform := "linux/x86_64"

# Show available commands.
default:
    @just --list

# Build and push the forum release image.
forum-release:
    docker build --platform {{docker_platform}} -t {{forum_image}} {{repo_dir}}/forum_instance
    docker push {{forum_image}}

# Install Parser Studio and its development tools in an isolated uv environment.
studio-install:
    cd {{repo_dir}}/parser_studio && uv sync --extra dev

# Run Parser Studio unit tests.
studio-test:
    cd {{repo_dir}}/parser_studio && uv run pytest

# Open the local Parser Studio desktop application.
studio-run:
    cd {{repo_dir}}/parser_studio && uv run agromega-parser-studio
