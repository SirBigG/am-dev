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
