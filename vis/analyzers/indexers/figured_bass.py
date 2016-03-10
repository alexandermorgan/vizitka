#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           vis
# Program Description:    Helps analyze music with computers.
#
# Filename:               analyzers/indexers/figured_bass.py
# Purpose:                Figured bass indexer
#
# Copyright (C) 2016 Marina Borsodi-Benson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#--------------------------------------------------------------------------------------------------
"""
.. codeauthor:: Marina Borsodi-Benson <marinaborsodibenson@gmail.com>
"""

import six
from music21 import stream
from vis.analyzers import indexer
from vis.analyzers.indexers import ngram
import pandas


def indexer_func(obj):
    """
    The function that indexes.

    :param obj: The simultaneous event(s) to use when creating this index. (For indexers using a
        :class:`Score`).
    :type obj: list of objects of the types stored in :attr:`TemplateIndexer._types`

    **or**

    :param obj: The simultaneous event(s) to use when creating this index. (For indexers using a
        :class:`Series`).
    :type obj: :class:`pandas.Series` of strings

    :returns: The value to store for this index at this offset.
    :rtype: str
    """
    return None


class FiguredBassIndexer(indexer.Indexer):

    required_score_type = 'pandas.DataFrame'
    possible_settings = ['horizontal']


    def __init__(self, score, settings=None):

        self.horiz_score = score['interval.HorizontalIntervalIndexer']
        self.vert_score = score['interval.IntervalIndexer']

        if settings is None:
            self._settings = {}
            self.horizontal_voice = len(self.horiz_score.columns) - 1
            self._settings['horizontal'] = len(self.horiz_score.columns) - 1
        else:
            self._settings = settings
            
        super(FiguredBassIndexer, self).__init__(score, None)


    def run(self):

        pairs = []
        intervals = []
        results = self.horiz_score[str(self.horizontal_voice)]
        intervals.append(results.tolist())

        for pair in list(self.vert_score.columns.values):
            if str(self.horizontal_voice) in pair:
                pairs.append(pair)

        for pair in pairs:
            intervals.append(self.vert_score[pair].tolist())

        intervals = zip(*intervals)
        pairs = str(self.horizontal_voice) + ' ' + ' '.join(pairs)

        result = pandas.DataFrame({pairs: pandas.Series([str(intvl) for intvl in intervals], index=self.horiz_score.index)})

        return self.make_return(result.columns.values, [result[name] for name in result.columns])