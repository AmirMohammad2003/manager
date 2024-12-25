import os
import subprocess
import logging
import json
import argparse
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DotfileManager:
    def __init__(self, repo_url=None, dotfiles_dir="dotfiles"):
        self.repo_url = repo_url
        self.dotfiles_dir = Path(dotfiles_dir).absolute()
        self.config_file = Path.home() / ".dotfile"
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                config = json.load(f)
                self.repo_url = config.get("repo_url", self.repo_url)
                self.dotfiles_dir = Path(
                    config.get("dotfiles_dir", self.dotfiles_dir)
                ).absolute()
        else:
            logging.info(f"No configuration file found at {self.config_file}")

    def save_config(self):
        dotfiles_path = str(self.dotfiles_dir.absolute())
        config = {
            "repo_url": self.repo_url,
            "dotfiles_dir": dotfiles_path,
        }
        with open(self.config_file, "w+") as f:
            json.dump(config, f)
        logging.info(f"Configuration saved to {self.config_file}")

    def clone_repo(self):
        if not os.path.exists(self.dotfiles_dir):
            logging.info(f"Cloning repository {self.repo_url} into {self.dotfiles_dir}")
            subprocess.run(
                ["git", "clone", self.repo_url, self.dotfiles_dir], check=True
            )
        else:
            logging.info(f"Repository already cloned in {self.dotfiles_dir}")

    def create_symlinks(self):
        for root, _, files in os.walk(self.dotfiles_dir):
            for file in files:
                dotfile_path = os.path.join(root, file)
                relative_path = os.path.relpath(dotfile_path, self.dotfiles_dir)
                target_path = os.path.expanduser(f"~/{relative_path}")

                if os.path.exists(target_path):
                    logging.warning(
                        f"Target path {target_path} already exists. Skipping."
                    )
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    os.symlink(dotfile_path, target_path)
                    logging.info(f"Created symlink: {target_path} -> {dotfile_path}")

    def update_repo(self):
        logging.info(f"Updating repository in {self.dotfiles_dir}")
        subprocess.run(
            ["git", "-C", self.dotfiles_dir, "add", "."],
            check=True,
        )
        changes = True
        try:
            subprocess.run(
                ["git", "-C", self.dotfiles_dir, "commit", "-m", '"Update config"'],
                check=True,
            )
        except Exception:
            logging.info("No changes to sync up.")
            changes = False

        try:
            subprocess.run(
                ["git", "-C", self.dotfiles_dir, "pull", "origin", "main", "--rebase"],
                check=True,
            )
        except Exception as e:
            print(e)
        if changes:
            subprocess.run(
                ["git", "-C", self.dotfiles_dir, "push", "origin", "main"],
                check=True,
            )

    def init(self):
        self.clone_repo()
        self.save_config()

    def add_dotfile(self, file_path):
        file_path = Path(file_path)
        if not file_path.is_absolute():
            file_path = file_path.resolve()
        target_path = self.dotfiles_dir / file_path.name
        if target_path.exists():
            logging.warning(f"Dotfile {target_path} already exists in the repository. Skipping.")
        else:
            os.makedirs(target_path.parent, exist_ok=True)
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            os.rename(file_path, backup_path)
            subprocess.run(["cp", backup_path, target_path], check=True)
            os.symlink(target_path, file_path)
            logging.info(f"Added dotfile: {file_path} -> {target_path}")
            self.update_repo()

    def add_folder(self, folder_path):
        folder_path = Path(folder_path)
        if not folder_path.is_absolute():
            folder_path = folder_path.resolve()
        target_path = self.dotfiles_dir / folder_path.name
        if target_path.exists():
            logging.warning(f"Folder {target_path} already exists in the repository. Skipping.")
        else:
            os.makedirs(target_path.parent, exist_ok=True)
            if (folder_path / ".git").exists():
                subprocess.run(["git", "submodule", "add", folder_path, target_path], check=True)
                logging.info(f"Added folder as sub-repo: {folder_path} -> {target_path}")
            else:
                subprocess.run(["cp", "-r", folder_path, target_path], check=True)
                logging.info(f"Added folder: {folder_path} -> {target_path}")
                os.symlink(target_path, folder_path)
                logging.info(f"Created symlink: {folder_path} -> {target_path}")
            self.update_repo()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage your dotfiles")
    parser.add_argument(
        "--sync", action="store_true", help="Update the dotfiles repository"
    )
    parser.add_argument("--init", help="Initialize with the given repository URL")
    parser.add_argument("-d", help="Clone the repository in the given directory")
    parser.add_argument("--add", help="Add a dotfile or folder to the repository")
    args = parser.parse_args()

    if args.sync:
        manager = DotfileManager()
        manager.update_repo()
    elif args.init is not None and args.d is not None:
        manager = DotfileManager(
            args.init,
        )
        manager.init()
    elif args.add:
        manager = DotfileManager()
        add_path = Path(args.add)
        if add_path.is_dir():
            manager.add_folder(add_path)
        else:
            manager.add_dotfile(add_path)
    else:
        # TODO: print usage
        pass
