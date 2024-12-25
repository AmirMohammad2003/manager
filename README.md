# Dotfile Manager

This is a simple Python script for managing your dotfiles. It allows you to clone a repository, create symlinks, update the repository, add dotfiles, and add folders.

## Installation

1. Clone the repository:
    ```sh
    git clone <repository-url>
    ```

2. Navigate to the repository directory:
    ```sh
    cd <repository-directory>
    ```

3. Make the `dotfiles` script executable:
    ```sh
    chmod +x dotfiles
    ```

## Usage

Here are some examples of how to use the `dotfiles` script:

1. Initialize with a given repository URL:
    ```sh
    ./dotfiles --init <repository-url> -d <directory>
    ```

2. Update the dotfiles repository:
    ```sh
    ./dotfiles --sync
    ```

3. Add a dotfile to the repository:
    ```sh
    ./dotfiles --add <file-path>
    ```

4. Add a folder to the repository:
    ```sh
    ./dotfiles --add <folder-path>
    ```

## Note

This is a hobby project created in an afternoon. It is probably not what you are looking for, and there are much better and more sophisticated tools out there.
