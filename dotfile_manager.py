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
        self.meta_data_file = self.dotfiles_dir / "metadata.json"
        self.meta_data = []
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                config = json.load(f)
                self.repo_url = config.get("repo_url", self.repo_url)
                self.dotfiles_dir = Path(
                    config.get("dotfiles_dir", self.dotfiles_dir)
                ).absolute()
                self.meta_data_file = self.dotfiles_dir / "metadata.json"
        else:
            logging.info(f"No configuration file found at {self.config_file}")

    def get_metadata(self):
        if os.path.exists(self.meta_data_file):
            with open(self.meta_data_file, "r") as f:
                self.meta_data = json.load(f)
        else:
            self.meta_data = []
        return self.meta_data

    def add_to_metadata(self, data):
        data = str(data)
        self.get_metadata()
        self.meta_data.append(data)
        with open(self.meta_data_file, "w") as f:
            json.dump(self.meta_data, f)

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
        for file in self.get_metadata():
            file = Path(file)
            if os.path.exists(file):
                logging.warning(f"Target path {file} already exists. Skipping.")
            else:
                dotfile_path = self.dotfiles_dir / file.relative_to("/")
                os.makedirs(os.path.dirname(file), exist_ok=True)
                os.symlink(dotfile_path, file)
                logging.info(f"Created symlink: {file} -> {dotfile_path}")

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
        self.create_symlinks()

    def init(self):
        self.clone_repo()
        self.save_config()

    def add_dotfile(self, file_path):
        file_path = Path(file_path)
        if not file_path.is_absolute():
            file_path = file_path.resolve()
        target_path = self.dotfiles_dir / file_path.relative_to("/")
        if target_path.exists():
            logging.warning(
                f"Dotfile {target_path} already exists in the repository. Skipping."
            )
        else:
            self.add_to_metadata(file_path)
            os.makedirs(target_path.parent, exist_ok=True)
            backup_path = file_path.with_suffix(str(file_path.suffix) + ".bak")
            os.rename(file_path, backup_path)
            subprocess.run(["cp", backup_path, target_path], check=True)
            logging.info(f"Added dotfile: {file_path} -> {target_path}")
            self.update_repo()

    def add_folder(self, folder_path):
        folder_path = Path(folder_path)
        if not folder_path.is_absolute():
            folder_path = folder_path.resolve()
        target_path = self.dotfiles_dir / folder_path.relative_to("/")
        if target_path.exists():
            logging.warning(
                f"Folder {target_path} already exists in the repository. Skipping."
            )
        else:
            if (folder_path / ".git").exists():
                # Git repositories aren't supported
                pass
            else:
                self.add_to_metadata(folder_path)
                os.makedirs(target_path.parent, exist_ok=True)
                subprocess.run(["cp", "-r", folder_path, target_path], check=True)
                logging.info(f"Added folder: {folder_path} -> {target_path}")
                # back up the folder
                subprocess.run(
                    ["mv", folder_path, str(folder_path) + ".bak"], check=True
                )
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

    script_path = Path(__file__).absolute()

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
