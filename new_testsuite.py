#!/usr/bin/env python3
"""
Helper to create a skeleton testsuite for a GNOME module.

NOTE: openQA testing for GNOME modules is still a prototype.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from shutil import copy

log = logging.getLogger()

# Files to copy into the new testsuite.

CONFIG_FILES = [
    "smbios.txt"
]

LIB_FILES = [
    "app_test.pm",
    "gnomeosdistribution.pm",
    "gnomeutils.pm",
    "serial_terminal.pm",
]

TESTS_FILES = [
    "gnome_welcome.pm",
    "gnome_disable_update_notification.pm",
    "gnome_desktop.pm",
    "show_core_dumps.pm",
]

NEEDLES = [
    "desktop_empty",
    "desktop_runner",
    "gnome_firstboot_welcome",
    "gnome_firstboot_language",
    "gnome_firstboot_privacy",
    "gnome_firstboot_timezone_1",
    "gnome_firstboot_timezone_2",
    "gnome_firstboot_aboutyou_1",
    "gnome_firstboot_aboutyou_2",
    "gnome_firstboot_password_1",
    "gnome_firstboot_password_2",
    "gnome_firstboot_complete",
    "gnome_desktop_tour",
    "gnome_desktop_installer",
    "gnome_desktop_desktop",
]


CONFIG_TEMPLATE="""
products:
  gnomeos:
    distri: gnomeos
    flavor: iso
    version: "master"
    arch: "x86_64"

machines:
  qemu_x86_64:
    backend: "qemu"
    settings:
      CDMODEL: scsi-cd
      DESKTOP: gnomeos
      HDDMODEL: virtio-blk
      HDDSIZEGB: '40'
      NICMAC: 52:54:00:12:34:56
      NICMODEL: virtio-net
      NICTYPE: user
      NICVLAN: '0'
      NUMDISKS: '1'
      PART_TABLE_TYPE: gpt
      QEMUCPU: host
      QEMUCPUS: '2'
      QEMUPORT: '20012'
      QEMURAM: '2560'
      QEMU_SMBIOS: 'type=11,path=/tests/config/smbios.txt'
      QEMU_VIDEO_DEVICE: virtio-vga
      UEFI: '1'
      UEFI_PFLASH_CODE: /usr/share/qemu/ovmf-x86_64-code.bin
      UEFI_PFLASH_VARS: /usr/share/qemu/ovmf-x86_64-vars.bin
      VIRTIO_CONSOLE: '1'
      VNC_TYPING_LIMIT: '5'

job_templates:
  {testsuite_name}:
    product: gnomeos
    machine: qemu_x86_64
    settings:
      ISO: /disk.iso
"""


MAIN_TEMPLATE="""
use Mojo::Base -strict;

use autotest;
use testapi;

my $distri = testapi::get_required_var('CASEDIR') . '/lib/gnomeosdistribution.pm';
require $distri;
testapi::set_distribution(gnomeosdistribution->new);

$testapi::username = 'testuser';
$testapi::password = 'testingtesting123';

my $testsuite = testapi::get_required_var('TEST');

if ($testsuite eq "{testsuite_name}") {
    $testapi::form_factor_postfix = '';
    autotest::loadtest("tests/gnome_welcome.pm");
    autotest::loadtest("tests/gnome_disable_update_notification.pm");
    autotest::loadtest("tests/gnome_desktop.pm");
    autotest::loadtest("tests/show_core_dumps.pm");
} else {
    die("Invalid testsuite: '$testsuite'");
}

1;
"""

def argument_parser():
    default_dest = Path("./tests/openqa")

    parser = argparse.ArgumentParser(description="new_testsuite")
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help="Enable detailed logging to stderr")
    parser.add_argument('-t', '--openqa-tests', type=Path, required=True,
                        help="Path to a GNOME/openqa-tests.git clone")
    parser.add_argument('-n', '--openqa-needles', type=Path,
                        help="Path to a GNOME/openqa-needles.git clone (default: openqa-tests.git/needles)")
    parser.add_argument('-d', '--dest', type=Path, default=default_dest,
                        help=f"Location to create the new testsuite (default: {default_dest})")
    parser.add_argument('--name', required=True, help="Testsuite name")
    return parser


def latest_needle_basename(needle_dir: Path, needle_tag: str) -> str:
    """Return the newest needle file with the given tag.

    Needle filenames are expected to follow the pattern:

      * {tag}.json
      * {tag}-{updatedatetime}.json
    """

    glob_text = f"{needle_tag}-*.json"
    needle_files_with_date = list(needle_dir.glob(glob_text))

    glob_text = f"{needle_tag}.json"
    needle_file_og = list(needle_dir.glob(glob_text))

    if len(needle_files_with_date) > 1:
        latest_needle_file = list(sorted(needle_files_with_date))[-1]
    elif len(needle_file_og) > 0:
        latest_needle_file = needle_file_og[0]
    logging.debug("Latest needle: %s", latest_needle_file)
    return Path(latest_needle_file).stem


def main():
    args = argument_parser().parse_args()

    if args.debug:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    dest = args.dest
    openqa_tests = args.openqa_tests
    openqa_needles = args.openqa_needles or openqa_tests.joinpath("needles")
    testsuite_name = args.name
    logging.info("openqa_tests dir: %s. openqa_needles dir: %s. dest dir: %s",
                 openqa_tests, openqa_needles, dest)

    dest.mkdir(exist_ok=True)

    dest_config = dest.joinpath("config")
    dest_config.mkdir(exist_ok=True)
    for config_file in CONFIG_FILES:
        copy(openqa_tests.joinpath("config", config_file), dest_config)
    dest_config.joinpath("scenario_definitions.yaml").write_text(
        CONFIG_TEMPLATE.replace("{testsuite_name}", testsuite_name)
    )

    dest_lib = dest.joinpath("lib")
    dest_lib.mkdir(exist_ok=True)
    for lib_file in LIB_FILES:
        copy(openqa_tests.joinpath("lib", lib_file), dest_lib)

    dest_tests = dest.joinpath("tests")
    dest_tests.mkdir(exist_ok=True)
    for tests_file in TESTS_FILES:
        copy(openqa_tests.joinpath("tests", tests_file), dest_tests)

    dest_needles = dest.joinpath("needles")
    dest_needles.mkdir(exist_ok=True)
    for needle in NEEDLES:
        needle_basename = latest_needle_basename(openqa_needles, needle)
        copy(openqa_needles.joinpath(f"{needle_basename}.json"), dest_needles)
        copy(openqa_needles.joinpath(f"{needle_basename}.png"), dest_needles)

    dest.joinpath("main.pm").write_text(
        MAIN_TEMPLATE.replace("{testsuite_name}", testsuite_name)
    )


try:
    main()
except RuntimeError as e:
    sys.stderr.write("ERROR: {}\n".format(e))
    sys.exit(1)
