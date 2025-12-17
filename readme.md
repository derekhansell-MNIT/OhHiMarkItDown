# OhHiMarkItDown

My attempt at a vibe-coded (mostly by Copilot) pipeline to convert .docx documents to markdown to facilitate a move from SharePoint Document Libraries to a GitHub knowledge repo.
Uses [MarkItDown](https://github.com/microsoft/markitdown) for the initial .md conversion and other existing Python packages to complete image extraction and re-insertion.

# Prereqs
 - Only runs on Windows (for now)
 - Python 3.10+
 - Git for Windows
 - Latest version of markitdown repo cloned into ./markitdown. Setup.py will attempt to do this for you.

# How to use

1) Clone repo
2) Run setup.py
3) Switch to dark mode
4) Select source and destination directories
5) 6) Click Run Conversion
   <img width="881" height="517" alt="image" src="https://github.com/user-attachments/assets/803d78b4-cfb9-4bf4-ab26-4536f57cb460" />

# How it works

 - Creates virtual environment directory ./venv in cloned repo diectory
 - Configures pre-reqs in requirements.txt
 - Clones markitdown repo and locally installs markitdown[docx]
 - Launches GUI app
 - Recreates source directory folder structure in destination directory
 - Runs MarkItDown recursively on .docx files in the source directory and puts the output in the destination directory
 - Assigns a UUID to each document
 - Extracts images into folders in dest_dir/.media folder that correspond to the UUID of each document and creates numbered placholder lines in the .md file
 - Rewrites the image links in the .md with a pretty high degree of accuracy

# Known issues

 - Image extraction and re-insertion isn't 100% accurate. I spent a ton of time getting it to be as accurate as possible across as many documents as possible, but check its work and update the image link locations as needed.
 - Tables embeded in .docx files can be very hit or miss. I'd love some help improving that functionality.
 - Documents containing xml or html meant as reference material, e.g., the xml for the Office Customization Tool or unattended Windows installs, etc., will most likely be incorrectly interpreted and not appear correctly inthe markdown preview. No current way to address this without pre-sanitizing your documents somehow. You'll need to go mark this code off with backticks. I will work on detecting, logging, and flagging these in documents in the future.
