"""
MIT License

Copyright (c) 2024 UnifierHQ

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import nextcord

class ActionRow:
    """A basic reimplementation of Novus' ActionRow."""

    def __init__(self, *args):
        if len(args) > 5:
            raise ValueError("too many items")
        if len(args) < 0:
            raise ValueError("no items")

        self.items = list(args)

class MessageComponents(nextcord.ui.View):
    """An extension of nextcord.ui.View to support custom ActionRow implementation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.row_count = 0
        self.auto_defer = False

    def add_rows(self, *rows: ActionRow):
        for row in rows:
            self.add_row(row)

        return self.row_count

    def add_row(self, row: ActionRow):
        if len(self.children)==0:
            self.row_count = 0

        if self.row_count >= 5:
            raise ValueError('cannot add more rows')

        for item in row.items:
            item.row = self.row_count
            self.add_item(item)

        self.row_count += 1
        return self.row_count

class View(MessageComponents):
    """Alias for View"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def view_constructor(*args):
    """Constructs a View with rows"""

    view = View()
    view.add_rows(*args)
    return view
