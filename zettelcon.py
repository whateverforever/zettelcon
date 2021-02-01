import datetime
import glob
import os
import re
import time
from argparse import ArgumentParser
from collections import defaultdict
from multiprocessing import Pool
from pprint import pformat

BACKLINK_START = "## Backlinks"
# ASSUMES the standard zettlr wikilink syntax for links
REX_LINK = re.compile(r"\[\[(.+?)\]\]")
# ASSUMES the standard single-line hashtag syntax for titles
REX_TITLE = re.compile(r"^#\s+(.+)")
REX_LINECLEANER = re.compile(r"^\s*(\*|-|\+|\d+\.|>) (\[ \]|\[x\])? *")
REX_TRAILINGNEWLINES = re.compile(r"(\n*)\Z", re.MULTILINE)

NOWSTR = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")


def main():
    parser = ArgumentParser(
        description="Tool to insert automatic backlinks into Zettlr note collections or other interlinked markdown files."
    )
    parser.add_argument(
        "-f",
        "--folder",
        help="Path to folder with all the zettels in it. Defaults to current directory.",
        default=".",
    )
    parser.add_argument(
        "-s",
        "--suffix",
        help="Suffix for the files to consider. Defaults to .md",
        default=".md",
    )
    parser.add_argument(
        "-c",
        "--clear-backlinks",
        help="Instead of generating backlinks, revert all files to a no-backlinks state",
        action="store_true",
    )
    parser.add_argument(
        "-n",
        "--nprocs",
        help="Number of worker processes to run for file reading and writing.",
        default=2,
        type=int,
    )

    args = parser.parse_args()
    params = vars(args)

    process_directory(**params)


def process_directory(folder, suffix, nprocs, clear_backlinks=False):
    t_start = time.time()
    files = glob.glob(os.path.join(folder, f"*{suffix}"))
    pool = Pool(processes=nprocs)

    if clear_backlinks:
        pool.map(clear_backlinks_from_file, files)
        print("Cleared backlinks from all files")
        return

    links = []
    res = pool.map(get_file_outlinks, files)

    for outlinks in res:
        links.extend(outlinks)

    links = change_ids_to_filepaths(links, files)
    backlinks_per_targetfile = bundle_backlinks_per_targetfile(links)

    pool.map(write_backlinks_to_file, backlinks_per_targetfile.values())

    unreferenced_files = set(files) - set(backlinks_per_targetfile.keys())
    pool.map(clear_backlinks_from_file, unreferenced_files)

    t_end = time.time()
    duration = t_end - t_start
    print(
        f"\nWrote {len(links)} backlinks from/to {len(files)} files in {duration:.2f}s"
    )


def clear_backlinks_from_file(filepath):
    write_backlink_section_to_file("", filepath)


def bundle_backlinks_per_targetfile(links):
    """
    Takes a list of backlinks that contain metadata about source and target file.
    Returns a dict that maps target file names to backlinks which point to it.
    """
    backlinks_for_file = defaultdict(list)

    for link_i in links:
        filename = link_i["link_target"]
        backlinks_for_file[filename].append(link_i)

    return backlinks_for_file


def write_backlinks_to_file(backlinks):
    """
    ASSUMES all the backlinks point to the same file
    """

    target_file = backlinks[0]["link_target"]
    backlinks_by_src = defaultdict(list)

    for backlink in backlinks:
        backlinks_by_src[backlink["link_source"]].append(backlink)

    entries = []
    for source_file, src_backlinks in backlinks_by_src.items():
        source_file_title = src_backlinks[0]["link_source_title"]
        source_file_relative = os.path.relpath(
            source_file, start=os.path.dirname(target_file)
        )
        entry = "> - [{}]({})\n".format(source_file_title, source_file_relative)

        for backlink in src_backlinks:
            # ASSUMES two spaces are used for list indentation
            entry += ">   - {}\n".format(backlink["link_context"])

        entries.append(entry)

    backlink_section = f"{BACKLINK_START}\n\n"
    backlink_section += ">    \n".join(entries)

    backlink_section += f"\n_Backlinks last generated {NOWSTR}_\n"

    write_backlink_section_to_file(backlink_section, target_file)


def write_backlink_section_to_file(section_text, filepath):
    with open(filepath, "r", encoding="utf-8") as fh:
        contents = fh.read()

    with open(filepath, "w", encoding="utf-8") as fh:
        try:
            backlink_sec_idx = contents.index(BACKLINK_START)
        except ValueError:
            # no backlink section in file
            backlink_sec_idx = None

        main_content = contents[:backlink_sec_idx]
        res = REX_TRAILINGNEWLINES.search(main_content)

        num_existing_newlines = len(res.group(1))
        num_needed_newlines = max(2 - num_existing_newlines, 0)

        backlink_section = "\n" * num_needed_newlines
        backlink_section += section_text

        # ASSUMES backlink section is last part of page
        contents_backlinked = main_content + backlink_section
        fh.write(contents_backlinked)


def change_ids_to_filepaths(links, all_filenames):
    out = []

    for entry in links:
        target_candidates = []

        for filename in all_filenames:
            if entry["link_target"] in filename:
                target_candidates.append(filename)

        # ASSUMES note IDs are unique, also among rest of file names
        if len(target_candidates) == 1:
            entry["link_target_orig"] = entry["link_target"]
            entry["link_target"] = target_candidates[0]
            out.append(entry)
        elif len(target_candidates) == 0:
            print("NO TARGET FOUND FOR {}".format(pformat(entry)))
            pass  # no possible target found
        elif len(target_candidates) > 1:
            print(
                "MULTIPLE TARGETS FOUND FOR {}: {}".format(
                    entry, pformat(target_candidates)
                )
            )
            pass  # multiple targets found

    return out


def get_file_outlinks(path):
    with open(path, "r", encoding="utf-8") as fh:
        contents = fh.read()

    paragraphs = [para.strip() for para in contents.split("\n")]

    outlinks = []
    first_header = ""

    for para in paragraphs:
        reached_backlink_section = BACKLINK_START in para
        if reached_backlink_section:
            break

        if first_header == "":
            res = REX_TITLE.match(para)
            if res:
                first_header = res.group(1)

        links = find_links_in_text(para)
        links = [
            {"link_source_title": first_header, "link_source": path, **entry}
            for entry in links
        ]
        outlinks.extend(links)

    return outlinks


def find_links_in_text(paragraph):
    clean_para = REX_LINECLEANER.sub("", paragraph)

    out = []
    for res in REX_LINK.finditer(paragraph):
        link = {
            "link_target": res.group(1),
            "link_context": clean_para,
            "context_pos_start": res.start(),
            "context_pos_end": res.end(),
        }

        out.append(link)

    return out


if __name__ == "__main__":
    main()
