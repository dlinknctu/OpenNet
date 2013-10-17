#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from subprocess import call
VERSION = "0.1"
NS3_PATH = "https://www.nsnam.org/release/"
NS3_FILE = "ns-allinone-3.18.tar.bz2"
PATCH_PATH = "https://raw.github.com/dlinknctu/OpenNet/dev/"
PATCH_FILE = ["animation-interface.patch", "packet-metadata.patch", "sta-wifi-scan.patch"]

def info(msg):
	print("\033[32m" + msg + "\033[0m")

def main():
  info("Welcome to OpenNet Installer")
  info("Fetch ns-3 source code")
  call(["curl", "-L", NS3_PATH+NS3_FILE, "-o", NS3_FILE])
  info("Extract ns-3 source code")
  call(["tar", "jxf", NS3_FILE])
  info("Apply patches")

  for patch in PATCH_FILE:
		call(["curl", "-L", PATCH_PATH+patch, "-o", patch])
    call(["patch", "-p1", "-i", patch])

  info("Installation finished. Have a nice day :)")

if __name__ == '__main__':
    main()