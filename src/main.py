#!/usr/bin/env python3
import sqlite3

import urwid

from scroll import Scrollable
from scroll import ScrollBar

cursor = ""


def load_bible_chapter():
    (book_number, chapter_number) = get_current_position()
    bible_chapter = get_bible_chapter(False, "kjv", book_number, chapter_number)
    return bible_chapter


def get_next_bible_chapter():
    (book_number, chapter_number) = get_current_position()
    bible_chapter = get_bible_chapter(False, "kjv", book_number, (chapter_number + 1))
    return bible_chapter


def get_bible_chapter(
    show_verse_numbers: bool, version: str, book_number: int, chapter_number: int
) -> list:
    bible_chapter = []
    if show_verse_numbers is True:
        for row in cursor.execute(
            f"select v,t from t_{version} where b is {book_number} and c is {chapter_number}"
        ):
            verse = row[0]
            text = row[1]
            bible_chapter.append(f" |{verse}| {text}")
    else:
        for row in cursor.execute(
            f"select t from t_{version} where b is {book_number} and c is {chapter_number}"
        ):
            text = row[0]
            bible_chapter.append(f"{text} ")
    set_current_position(book_number, chapter_number)
    return bible_chapter


def init_database():
    global cursor
    connection = sqlite3.connect("data.db")
    cursor = connection.cursor()
    # Add custom table for keeping track of reading position.
    cursor.execute(
        "create table if not exists current_position("
        "current_book int PRIMARY KEY,"
        "current_chapter int NOT NULL)"
    )


def set_current_position(book_number, chapter_number) -> None:
    print(f"insert into current_position ({book_number},{chapter_number})")
    cursor.execute(
        f"insert or replace into current_position(current_book,current_chapter) values({book_number},{chapter_number})"
    )


def get_current_position():
    for data in cursor.execute(
        "select current_book,current_chapter from current_position"
    ):
        current_book_number = data[0]
        current_chapter_number = data[1]
    current_position = (current_book_number, current_chapter_number)
    return current_position


#  def show_or_exit(key):
#      if key in ("q", "Q"):
#          raise urwid.ExitMainLoop()
#      txt.set_text(repr(key))


def main():
    init_database()
    bible_chapter = load_bible_chapter()
    main = urwid.Text(bible_chapter)
    #  mainloop = urwid.MainLoop(ScrollBar(Scrollable(main)), unhandled_input=show_or_exit)
    mainloop = urwid.MainLoop(ScrollBar(Scrollable(main)))
    mainloop.run()


if __name__ == "__main__":
    main()
