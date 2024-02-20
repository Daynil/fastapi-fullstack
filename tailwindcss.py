import platform
import shlex
import subprocess
from pathlib import Path

import httpx
import rich.progress


def run_cmd(command: str | list[str], print_output=True, input=None):
    if isinstance(command, str):
        command = shlex.split(command)

    process = subprocess.run(command, capture_output=True, input=input, text=True)

    if print_output:
        print(process.stdout)
        if process.stderr:
            print(process.stderr)


def download_file(url: str, dest: Path | str, follow_redirects=False):
    if isinstance(dest, str):
        dest = Path(dest)
    with dest.open("wb") as f:
        with httpx.stream("GET", url, follow_redirects=follow_redirects) as res:
            if res.status_code >= 300:
                res.read()
                raise Exception(res.status_code, res.text)

            total = int(res.headers["Content-Length"])

            with rich.progress.Progress(
                "[progress.percentage]{task.percentage:>3.0f}%",
                rich.progress.BarColumn(bar_width=None),
                rich.progress.DownloadColumn(),
                rich.progress.TransferSpeedColumn(),
            ) as progress:
                dl_task = progress.add_task("dl", total=total)
                for chunk in res.iter_bytes():
                    f.write(chunk)
                    progress.update(dl_task, completed=res.num_bytes_downloaded)


def install(version="latest"):
    """
    Select the appropriate build based on os and architecture.
    See os name conventions in tailwind blog.



    https://tailwindcss.com/blog/standalone-cli
    https://github.com/timonweb/pytailwindcss/tree/main
    """

    os_name = (
        platform.system().lower().replace("win32", "windows").replace("darwin", "macos")
    )
    ext = ".exe" if os_name == "windows" else ""

    arch = platform.machine().lower()

    binary_name = {
        "amd64": f"{os_name}-x64{ext}",
        "x86_64": f"{os_name}-x64{ext}",
        "arm64": f"{os_name}-arm64",
        "aarch64": f"{os_name}-arm64",
    }[arch]

    if version == "latest":
        url = f"https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-{binary_name}"
    else:
        url = f"https://github.com/tailwindlabs/tailwindcss/releases/download/{version}/tailwindcss-{binary_name}"

    print(f"Downloading tailwind bin {binary_name} at {url}...")
    download_file(url, "tailwindcss", follow_redirects=version == "latest")

    run_cmd("chmod +x tailwindcss")
    run_cmd("./tailwindcss init")


if __name__ == "__main__":
    install()
