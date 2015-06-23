import pandas as pd
import numpy as np
import os
import uuid
import json

from IPython.display import display_html, display_javascript


def template_contents(filename):
    template_filepath = os.path.join(
        os.path.dirname(__file__),
        'templates',
        filename,
    )
    with open(template_filepath) as f:
        return f.read()


SLICK_GRID_CSS = template_contents('slickgrid.css.template')
SLICK_GRID_JS = template_contents('slickgrid.js.template')

SLICK_GRID_DEFAULT_OPTIONS = {
    'enableCellNavigation': True,
    'fullWidthRows': True,
    'syncColumnCellResize': True,
    'forceFitColumns': True,
    'rowHeight': 28,
    'enableColumnReorder': False,
    'enableTextSelectionOnCells': True, }


def show_grid(data_frame, *args, **kwargs):
    return SlickGrid(data_frame, *args, **kwargs)


class SlickGrid(object):

    def __init__(self, data_frame, remote_js=False, precision=None,
                 options={}):
        self.data_frame = data_frame
        self.remote_js = remote_js
        self.div_id = str(uuid.uuid4())

        self.df_copy = data_frame.copy()

        if type(self.df_copy.index) == pd.core.index.MultiIndex:
            self.df_copy.reset_index(inplace=True)
        else:
            self.df_copy.insert(0, self.df_copy.index.name, self.df_copy.index)

        tc = dict(np.typecodes)
        for key in np.typecodes.keys():
            if "All" in key:
                del tc[key]

        self.column_types = []
        for col_name, dtype in self.df_copy.dtypes.iteritems():
            column_type = {'field': col_name}
            for type_name, type_codes in tc.items():
                if dtype.kind in type_codes:
                    column_type['type'] = type_name
                    break
            self.column_types.append(column_type)

        if isinstance(precision, int) and precision>=0:
            self.precision = precision
        elif precision is None:
            self.precision = pd.get_option('display.precision') - 1
        else:
            raise TypeError('precision')

        if not isinstance(options, dict):
            raise TypeError('options')
        self.options = SLICK_GRID_DEFAULT_OPTIONS.copy()
        self.options.update(options)

    def _ipython_display_(self):
        try:
            column_types_json = json.dumps(self.column_types)
            data_frame_json = self.df_copy.to_json(
                orient='records',
                date_format='iso',
                double_precision=self.precision,
            )
            options_json = json.dumps(self.options)

            if self.remote_js:
                cdn_base_url = \
                    "https://cdn.rawgit.com/quantopian/qgrid/ddf33c0efb813cd574f3838f6cf1fd584b733621/qgrid/qgridjs/"
            else:
                cdn_base_url = "/nbextensions/qgridjs"

            raw_html = SLICK_GRID_CSS.format(
                div_id=self.div_id,
                cdn_base_url=cdn_base_url,
            )
            raw_js = SLICK_GRID_JS.format(
                cdn_base_url=cdn_base_url,
                div_id=self.div_id,
                data_frame_json=data_frame_json,
                column_types_json=column_types_json,
                options_json=options_json,
            )

            display_html(raw_html, raw=True)
            display_javascript(raw_js, raw=True)
        except Exception as err:
            display_html('ERROR: {}'.format(str(err)), raw=True)
