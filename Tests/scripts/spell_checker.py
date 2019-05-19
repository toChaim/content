#!/usr/bin/env python3
import sys
import yaml
import enchant
import argparse

from Tests.test_utils import print_error

ENGLISH = enchant.Dict("en_US")
DISPLAYABLE_LINES = [
    "description",
    "name",
    "display",
    "comment"
]


def check_yaml(yml_info, unknown_words):
    for key, value in yml_info.items():
        if key in DISPLAYABLE_LINES:
            for word in value.split():
                if word.isalpha() and not ENGLISH.check(word):
                    unknown_words.add(word)

        else:
            if isinstance(value, dict):
                check_yaml(value, unknown_words)
            elif isinstance(value, list):
                for sub_list in value:
                    if isinstance(sub_list, dict):
                        check_yaml(sub_list, unknown_words)


def check_md_file(md_data, unknown_words):
    for line in md_data:
        for word in line.split():
            if word.isalpha() and not ENGLISH.check(word):
                unknown_words.add(word)


def spell_checker():
    description = """Run spell check on a given yml file. """
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-p", "--path", help="Specify path of yml/md file", required=True)
    parser.add_argument("-i", "--isMD", help="Whether the path is to a yml file or an md.", action='store_true')

    unknown_words = set([])
    args = parser.parse_args()

    if args.isMD:
        with open(args.path, 'r') as md_file:
            md_data = md_file.readlines()

        check_md_file(md_data, unknown_words)
    else:
        with open(args.path, 'r') as yaml_file:
            yml_info = yaml.safe_load(yaml_file)

        check_yaml(yml_info, unknown_words)

    if unknown_words:
        print_error(u"Found the problematic words:\n{}".format('\n'.join(unknown_words)))
        return 1

    print("No problematic words found")
    return 0


if __name__ == "__main__":
    sys.exit(spell_checker())
