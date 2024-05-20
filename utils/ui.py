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
