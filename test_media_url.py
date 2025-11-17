#!/usr/bin/env python3

"""
Generates URLs to GNOME OS disk images

This script generates URLs to a specific GNOME OS disk images, to be used from
testing pipelines instead of hard-coding URLs.
"""

import argparse

parser = argparse.ArgumentParser(description="URLs for GNOME test media")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--latest", action="store_true", help="Use latest")
group.add_argument("--stable-branch", type=str, help="Specify stable branch")
group.add_argument("--tag", type=str, help="Specify tag")
group.add_argument("--pipeline", type=int, help="Specify pipeline ID")
parser.add_argument(
    "--arch",
    default="x86_64",
    choices=["x86_64"],
    help="Specify architecture (x86_64 only for now)"
)

args = parser.parse_args()


def image_filename(arch) -> str:
    prefix = "gnome_os"
    return f"{prefix}_{arch}.iso"


version = args.tag or args.pipeline
if args.latest:
    filename = image_filename(args.arch)
    print(f"https://os.gnome.org/download/latest/{filename}")
elif args.stable_branch:
    filename = image_filename(args.arch)
    print(f"https://os.gnome.org/download/stable/{args.stable_branch}/{filename}")
else:
    print(f"https://os.gnome.org/download/{version}/gnome_os_{version}-x86_64.iso")
