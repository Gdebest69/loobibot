# Installation

## Install any requirements

 - [Python](https://www.python.org/downloads/) -  Any python version above 3.9 should work.
 - [Git](https://git-scm.com/downloads)
 
## Install the repository and necessary libraries

 1. Clone the repository: `git clone https://github.com/Gdebest69/loobibot.git`
 2. Go to the root directory: `cd loobibot`
 3. Install necessary libraries: `pip install -r requirements.txt`
 4. Install discord.py like shown below.
 5. There are a few missing files and folders which are essential for this repository to work, so you will have to personally ask me for them.

## How to install [discord.py](https://github.com/rapptz/discord.py) to make it work with my repository

### Option 1: install from my own fork of discord.py

 1. Clone the necessary discord.py repositories: `.\clone_fork_repo`. It should create a discord.py
 folder inside the root directory. To check if it worked:
 - Go to the discord.py folder: `cd discord.py`
 - Check for local git branches: `git branch`
 - The output should look like this:
 ```
   master
* merged
 ```
 - Go back to the root directory: `cd ..`
 2. (Optional) update the branch: `.\update_library`. It should merge successfully any new updates from the branches that I use in my repository without any conflicts. If there are conflicts you can try to resolve them manually if you feel like `him`, or just skip this step.
 3. Uninstall old versions of discord.py, if they exist.
- Run `pip list` and see if there are any packages listed named discord or discord.py.
- Uninstall the packages using `pip uninstall <package name>`. Example: `pip uninstall discord`
- Repeat the uninstall process until there aren't any packages named discord or discord.py listed when running `pip list`
4. Install the newly created package: `pip install discord.py\`

### Option 2: Install manually from discord.py (Hard)

 1. Clone the necessary discord.py repositories: `.\create_library`. It should create a discord.py
 folder inside the root directory. To check if it worked:
 - Go to the discord.py folder: `cd discord.py`
 - Check for local git branches: `git branch`
 - The output should look like this:
 ```
   master
* merged
 ```
 - Go back to the root directory: `cd ..`
 2. Install/update the branch: `.\update_library`. It will merge the necessary branches for my repository to work to the merged branch. You can also use it to update the branch.
> Note that the merge process may not work automatically on the first time, so you will have to resolve any conflicts manually. You can use a merge editor like the one VS Code provides, and add the conflicting lines together.
3. Uninstall old versions of discord.py, if they exist.
- Run `pip list` and see if there are any packages listed named discord or discord.py.
- Uninstall the packages using `pip uninstall <package name>`. Example: `pip uninstall discord`
- Repeat the uninstall process until there aren't any packages named discord or discord.py listed when running `pip list`
4. Install the newly created package: `pip install discord.py\`