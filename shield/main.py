# coding=UTF-8

import logging as log
import os

import argparse
import sqlite3
import urwid
import yaml

from shield import scroll

parser = argparse.ArgumentParser()
parser.add_argument(
    "-vv",
    help="Enable debug logging. Logs to shield.log at the current path",
    action="store_true",
)
parser.add_argument(
    "-v",
    help="Enable logging. Logs to shield.log at the current path",
    action="store_true",
)
args = parser.parse_args()

script_path = os.path.dirname(__file__)
current_position_file_path = os.path.join(script_path, "data/current_position.yaml")

# Read current position file. Create file if it doesn't exist.
if not os.path.exists(current_position_file_path):
    starting_position = {"v": "asv", "b": 43, "c": 1}
    with open(current_position_file_path, "w+", encoding="utf-8") as file:
        yaml.dump(starting_position, file)
with open(current_position_file_path, "r", encoding="utf-8") as file:
    current_position_config = yaml.safe_load(file)

database_path = os.path.join(script_path, "data/bible.db")
# Read config file values into variables for easier usage.
cfg_bible_version = current_position_config["v"]
cfg_book_number = current_position_config["b"]
cfg_chapter_number = current_position_config["c"]

# Configure logging.
if args.vv or args.v:
    if args.vv:
        LOG_LEVEL = "DEBUG"
    else:
        LOG_LEVEL = "INFO"
    log.basicConfig(
        filename="shield.log",
        format="%(asctime)s %(filename)s.%(funcName)s - %(message)s",
        level=LOG_LEVEL,
    )


# Initialize and connect to the database.
log.debug("Opening db at %s", database_path)
con = sqlite3.connect(database_path)


class Bible:
    """
    Main class for getting the Bible text.

    Args:
        bible_version (str): Bible version to use. By default reads the value
                             of "v" in data/current_position.yaml
        book_number (int): Book number by index. By default reads the value
                           of "b" in data/current_position.yaml
        chapter_number (int): Chapter number of the book by index. By default
                              reads the value of "c" in
                              data/current_position.yaml
    """

    def __init__(
        self,
        bible_version: str = cfg_bible_version,
        book_number: int = cfg_book_number,
        chapter_number: int = cfg_chapter_number,
    ):
        self.bible_version = bible_version
        self.book_number = book_number
        self.chapter_number = chapter_number

    def save_reading_position(self):
        """
        Saves the current reading position to current_position.yaml.
        """
        # Keep the key names short to minimize the amount of data we have to
        #   write each time we change chapters.
        current_position = {
            "v": self.bible_version,
            "b": self.book_number,
            "c": self.chapter_number,
        }
        log.debug("Writing current position to file")
        with open(current_position_file_path, "w+", encoding="utf-8") as current_file:
            yaml.dump(current_position, current_file)

    def get_next_chapter(self):
        """
        Returns the next chapter in sequence, switching books if necessary.
        """
        # If we've come to the end of Revelation, don't try going any further.
        if self.book_number == 66 and self.chapter_number == 22:
            raise ValueError("End of Bible!")

        log.debug(
            "Attempting to open chapter after %s",
            self.chapter_number,
        )
        self.chapter_number += 1

        for _ in range(2):
            output = self.get_chapter()
            # If the text of the chapter is empty, then we've come to the
            #   end of the book and need to switch to the next book.
            if len(output) == 0:
                self.book_number += 1
                self.chapter_number = 1
                log.info("Switching to book %s", self.book_number)
            else:
                return output
        raise RuntimeError("Unable to get next chapter!")

    def get_chapter(self) -> list:
        """
        Returns:
            Returns a list of strings, in which each string is a single verse.
        """
        log.debug("Getting book %s, chapter %s", self.book_number, self.chapter_number)
        output = []
        cursor = con.execute(
            f"SELECT t FROM t_{self.bible_version} WHERE b IS {self.book_number} AND c IS {self.chapter_number}"
        )
        for row in cursor:
            output.append(row[0])
            output.append(" ")
        self.save_reading_position()
        return output


def show_or_exit(key):
    if key in ("right"):
        try:
            text.set_text(bible.get_next_chapter())
        except ValueError:
            pass


# Render text.
bible = Bible()
chapter = bible.get_chapter()
text = urwid.Text(chapter)

main = urwid.Pile([("pack", text)])
mainloop = urwid.MainLoop(scroll.Scrollable(main), unhandled_input=show_or_exit)
mainloop.run()
