import logging
import subprocess
import os

def sync_files(restart: bool = False):
    """
    Synchronizes the Go application files from the MacBook to the Raspberry Pi
    and optionally restarts the Go application.
    """
    # ✅ Define correct Go project directory
    go_project_directory = "/Users/theokoester/dev/projects/FishReports/backend"
    remote_directory = "/home/theokoester/dev/FishReports/backend"

    ssh_command_create_dir = [
        "ssh",
        "theokoester@raspi",
        f"mkdir -p {remote_directory}"
    ]

    rsync_command = [
        "rsync",
        "-avz",
        "--delete",
        go_project_directory + "/",  # ✅ Use the correct source directory
        f"theokoester@raspi:{remote_directory}"
    ]

    try:
        logging.info("Ensuring remote directory exists...")
        subprocess.run(ssh_command_create_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("Remote directory checked/created successfully")

        # ✅ Set working directory to Go project directory
        logging.info("Compiling Go binary for Raspberry Pi (arm64)...")
        env = os.environ.copy()
        env["GOOS"] = "linux"
        env["GOARCH"] = "arm64"

        subprocess.run(["go", "build", "-o", "fishreports"], cwd=go_project_directory, check=True, env=env)

        logging.info("Starting rsync for Go application...")
        subprocess.run(rsync_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("Rsync completed successfully")

        if restart:
            ssh_command_restart = [
                "ssh",
                "theokoester@raspi",
                "sudo systemctl restart fishreports"
            ]
            logging.info("Restarting the Go application server...")
            subprocess.run(ssh_command_restart, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info("Go application server restarted successfully")

    except subprocess.CalledProcessError as e:
        logging.error("Error occurred during the operation")
        if e.stderr:
            logging.error(e.stderr.decode())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync_files(restart=True)
