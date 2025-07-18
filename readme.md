# OhHiMarkItDown

My attempt at a vibe-coded (mostly by Copilot) pipeline to convert .docx and .pdf documents to markdown to facilitate a move from SharePoint Document Libraries to a GitHub knowledge repo.
Uses [MarkItDown]([url](https://github.com/microsoft/markitdown)) for the initial .md conversion and other existing Python tools to complete image extraction and re-insertion.

# How to use

1) Clone repo
2) Run init.py
3) Select source and destination directories
4) Click Run Conversion
   <img width="881" height="517" alt="image" src="https://github.com/user-attachments/assets/803d78b4-cfb9-4bf4-ab26-4536f57cb460" />

# How it works

# Known issues

 - Image extraction and re-insertion isn't 100% accurate. I spent a ton of time getting it to be as accurate as possible across as many documents as possible, but check its work and update the image links as needed.
 - Tables embeded in .docx files can be very hit or miss. I'd love some help improving that functionality
 - Documents containing xml or html meant as reference material, e.g., the xml for the Office Customization Tool or unattended Windows installs, etc., will most  likely be incorrectly interpreted and not appear correctly inthe markdown preview. No current way to address this without pre-sanitizing your documents somehow. You'll need to go mark this code off with backticks. I will work on detecting, logging, and flagging these documents in the future.
