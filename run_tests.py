#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:              vis
# Program Description:       Measures sequences of vertical intervals.
#
# Filename: run_tests.py
# Purpose: Run the autmated tests for the models in vis.
#
# Copyright (C) 2012, 2013, 2014 Jamie Klassen, Christopher Antila
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
Run the tests for the models
"""

VERBOSITY = 1

# Imports
import unittest
from vis.tests import test_indexer, test_note_rest_indexer, test_ngram, test_repeat, \
    test_aggregator, test_interval_indexer, test_frequency_experimenter, test_offset, \
    test_lilypond
from vis.tests import test_indexed_piece, test_aggregated_pieces
from vis.tests import bwv2_integration_tests as bwv2
from vis.tests import test_workflow, test_workflow_integration, test_workflow_experiments

test_list = [ \
    # Indexer and Subclasses
    test_indexer.INDEXER_HARDCORE_SUITE,
    test_indexer.INDEXER_1_PART_SUITE,
    test_indexer.INDEXER_MULTI_EVENT_SUITE,
    test_indexer.UNIQUE_OFFSETS_SUITE,
    test_note_rest_indexer.NOTE_REST_INDEXER_SUITE,
    test_interval_indexer.INTERVAL_INDEXER_SHORT_SUITE,
    test_interval_indexer.INTERVAL_INDEXER_LONG_SUITE,
    test_interval_indexer.INT_IND_INDEXER_SUITE,
    test_interval_indexer.HORIZ_INT_IND_LONG_SUITE,
    test_repeat.REPEAT_INDEXER_SUITE,
    test_ngram.NGRAM_INDEXER_SUITE,
    test_offset.OFFSET_INDEXER_SINGLE_SUITE,
    test_offset.OFFSET_INDEXER_MULTI_SUITE,
    test_lilypond.ANNOTATION_SUITE,
    test_lilypond.ANNOTATE_NOTE_SUITE,
    test_lilypond.PART_NOTES_SUITE,
    test_lilypond.LILYPOND_SUITE,
    # Experimenter and Subclasses
    test_frequency_experimenter.FREQUENCY_FUNC_SUITE,
    test_frequency_experimenter.FREQUENCY_RUN_SUITE,
    test_aggregator.COLUMN_AGGREGATOR_SUITE,
    # IndexedPiece and AggregatedPieces
    test_indexed_piece.INDEXED_PIECE_SUITE_A,
    test_indexed_piece.INDEXED_PIECE_SUITE_B,
    test_indexed_piece.INDEXED_PIECE_PARTS_TITLES,
    test_aggregated_pieces.AGGREGATED_PIECES_SUITE,
    # WorkflowManager
    test_workflow.WORKFLOW_TESTS,
    test_workflow.GET_DATA_FRAME,
    test_workflow.EXPORT,
    test_workflow.EXTRA_PAIRS,
    test_workflow.SETTINGS,
    test_workflow.OUTPUT,
    test_workflow.AUX_METHODS,
    test_workflow_experiments.INTERVAL_NGRAMS,
    test_workflow_experiments.INTERVALS,
    # Integration Tests
    bwv2.ALL_VOICE_INTERVAL_NGRAMS,
    test_workflow_integration.INTERVALS_TESTS,
    test_workflow_integration.NGRAMS_TESTS,
    ]

# Test runner
for each_test in test_list:
    unittest.TextTestRunner(verbosity=VERBOSITY).run(each_test)
