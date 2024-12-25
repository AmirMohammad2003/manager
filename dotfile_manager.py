import os
import subprocess
import logging
import json
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DotfileManager:
    def __init__(self, repo_url=None, dotfiles_dir='dotfiles', config_file='config.json'):
        self.repo_url = repo_url
        self.dotfiles_dir = dotfiles_dir
        self.config_file = config_file
        self.load_config()
        if self.repo_url:
            self.clone_repo()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.repo_url = config.get('repo_url', self.repo_url)
        else:
            logging.info(f"No configuration file found at {self.config_file}")

    def save_config(self):
        config = {'repo_url': self.repo_url}
        with open(self.config_file, 'w') as f:
            json.dump(config, f)
        logging.info(f"Configuration saved to {self.config_file}")

    def clone_repo(self):
        if not os.path.exists(self.dotfiles_dir):
            logging.info(f"Cloning repository {self.repo_url} into {self.dotfiles_dir}")
            subprocess.run(['git', 'clone', self.repo_url, self.dotfiles_dir], check=True)
        else:
            logging.info(f"Repository already cloned in {self.dotfiles_dir}")

    def create_symlinks(self):
        for root, _, files in os.walk(self.dotfiles_dir):
            for file in files:
                dotfile_path = os.path.join(root, file)
                relative_path = os.path.relpath(dotfile_path, self.dotfiles_dir)
                target_path = os.path.expanduser(f"~/{relative_path}")

                if os.path.exists(target_path):
                    logging.warning(f"Target path {target_path} already exists. Skipping.")
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    os.symlink(dotfile_path, target_path)
                    logging.info(f"Created symlink: {target_path} -> {dotfile_path}")

    def update_repo(self):
        logging.info(f"Updating repository in {self.dotfiles_dir}")
        subprocess.run(['git', '-C', self.dotfiles_dir, 'pull'], check=True)

    def init_repo(self, repo_url):
        self.repo_url = repo_url
        self.clone_repo()
        self.save_config()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage your dotfiles")
    parser.add_argument('repo_url', nargs='?', help="GitHub repository URL for your dotfiles")
    parser.add_argument('--update', action='store_true', help="Update the dotfiles repository")
    parser.add_argument('--init', action='store_true', help="Initialize with the given repository URL")
    args = parser.parse_args()

    manager = DotfileManager(args.repo_url)
    if args.update:
        manager.update_repo()
    elif args.init and args.repo_url:
        manager.init_repo(args.repo_url)
    else:
        manager.create_symlinks()
        manager.save_config()
