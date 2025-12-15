import bs4

from src.preparer.remove_empty_tables import remove_empty_tables
from src._common.constants import CLS_METADATA_TABLE_JSONDATA, CLS_STATE_TABLE_JSONDATA
from src._common.state import DocumentState


HTML_STR = f"""<p class="dgt-mon-caption">Table 1: An empty table.</p>
<table>
  <tr>
    <td></td>
    <td></td>
  </tr>
  <tr>
    <td></td>
    <td></td>
  </tr>
  <tr>
    <td></td>
    <td></td>
  </tr>
</table>
<p class="dgt-mon-caption">Table 2: Not empty table.</p>
<table>
  <tr>
    <td>
      <p>Header 1</p>
    </td>
    <td>
      <p>Header 2</p>
    </td>
  </tr>
  <tr>
    <td>
      <p>Row 1, Column 1</p>
    </td>
    <td>
      <p>Row 1, Column 2</p>
    </td>
  </tr>
  <tr>
    <td>
      <p>Row 2, Column 1</p>
    </td>
    <td>
      <p>Row 2, Column 2</p>
    </td>
  </tr>
</table>
<script class="{CLS_METADATA_TABLE_JSONDATA}" hidden="hidden" type="application/json">[]</script>
<script class="{CLS_STATE_TABLE_JSONDATA}" hidden="hidden" type="application/json">[]</script>
"""


class TestRemovingEmptyTables:
    @classmethod
    def setup_class(cls):
        cls.html_soup = bs4.BeautifulSoup(HTML_STR, "html.parser")
        cls.tables = cls.html_soup.find_all("table")
        cls.dstate = DocumentState()
        cls.html_soup = remove_empty_tables(cls.html_soup, cls.dstate, cls.tables)
        cls.tables = cls.html_soup.find_all("table")

    def test_only_one_table_left(self):
        assert len(self.tables) == 1

    def test_empty_table_was_removed(self):
        # find next tag
        p = self.html_soup.find_all("p", string="Table 1: An empty table.")
        nxt = p[0].next_sibling
        while type(nxt) != bs4.element.Tag:
            nxt = nxt.next_sibling
        # check if next tag is an empty paragraph instead of a table
        assert nxt.name == "p"
        assert nxt.text == ""

    def test_nonempty_table_was_not_removed(self):
        # find next tag
        p = self.html_soup.find_all("p", string="Table 2: Not empty table.")
        nxt = p[0].next_sibling
        while type(nxt) != bs4.element.Tag:
            nxt = nxt.next_sibling
        # check if next tag is a table
        assert nxt.name == "table"
