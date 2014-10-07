#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           vis
# Program Description:    Helps analyze music with computers.
#
# Filename:               vis/tests/test_workflow.py
# Purpose:                Tests for the WorkflowManager
#
# Copyright (C) 2013, 2014 Christopher Antila, Alexander Morgan
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
.. codeauthor:: Christopher Antila <christopher@antila.ca>

Tests for the WorkflowManager
"""

# pylint: disable=protected-access

import os
from subprocess import CalledProcessError
from unittest import TestCase, TestLoader
import mock
from mock import MagicMock
import pandas
from pandas import Series, DataFrame
from music21.humdrum.spineParser import GlobalReference
from vis.workflow import WorkflowManager, split_part_combo
from vis.models.indexed_piece import IndexedPiece
from vis.analyzers.indexers import noterest, lilypond

# find the path to the 'vis' directory
import vis
VIS_PATH = vis.__path__[0]

# pylint: disable=R0904
# pylint: disable=C0111
class WorkflowTests(TestCase):
    """This class is for __init__(), load(), and run() (without helper methods) and split_part_combo()"""
    @mock.patch('vis.workflow.path.join', return_value='/some/vis/path.r')
    def test_init_1(self, mock_join):
        # with a list of basestrings
        # NB: mocked out os.path.join()
        with mock.patch('vis.models.indexed_piece.IndexedPiece') as mock_ip:
            in_val = ['help.txt', 'path.xml', 'why_you_do_this.rtf']
            test_wc = WorkflowManager(in_val)
            self.assertEqual(3, mock_ip.call_count)
            for val in in_val:
                mock_ip.assert_any_call(val)
            self.assertEqual(3, len(test_wc._data))
            for each in test_wc._data:
                self.assertTrue(isinstance(each, mock.MagicMock))
            self.assertEqual(3, len(test_wc._settings))
            for piece_sett in test_wc._settings:
                self.assertEqual(3, len(piece_sett))
                for sett in ['offset interval', 'voice combinations']:
                    self.assertEqual(None, piece_sett[sett])
                for sett in ['filter repeats']:
                    self.assertEqual(False, piece_sett[sett])
            exp_sh_setts = {'n': 2, 'continuer': 'dynamic quality', 'mark singles': False,
                            'interval quality': False, 'simple intervals': False,
                            'include rests': False, 'count frequency': True}
            self.assertEqual(exp_sh_setts, test_wc._shared_settings)
            self.assertEqual(1, mock_join.call_count)

    @mock.patch('vis.workflow.vis')
    def test_init_2(self, mock_vis):
        # with a list of IndexedPieces
        # NB: mocked out vis
        mock_vis.__path__ = ['/some/path/']
        exp_chart_path = '/some/path/scripts/R_bar_chart.r'
        in_val = [IndexedPiece('help.txt'), IndexedPiece('path.xml'),
                  IndexedPiece('why_you_do_this.rtf')]
        test_wc = WorkflowManager(in_val)
        self.assertEqual(3, len(test_wc._data))
        for each in test_wc._data:
            self.assertTrue(each in in_val)
        for piece_sett in test_wc._settings:
            self.assertEqual(3, len(piece_sett))
            for sett in ['offset interval', 'voice combinations']:
                self.assertEqual(None, piece_sett[sett])
            for sett in ['filter repeats']:
                self.assertEqual(False, piece_sett[sett])
        exp_sh_setts = {'n': 2, 'continuer': 'dynamic quality', 'mark singles': False,
                        'interval quality': False, 'simple intervals': False,
                        'include rests': False, 'count frequency': True}
        self.assertEqual(exp_sh_setts, test_wc._shared_settings)
        self.assertEqual(exp_chart_path, test_wc._R_bar_chart_path)

    def test_init_3(self):
        # with a mixed list of valid things
        # NB: ensure the _R_bar_chart_path actually exists
        in_val = [IndexedPiece('help.txt'), 'path.xml', 'why_you_do_this.rtf']
        test_wc = WorkflowManager(in_val)
        self.assertEqual(3, len(test_wc._data))
        self.assertEqual(in_val[0], test_wc._data[0])
        for each in test_wc._data[1:]:
            self.assertTrue(isinstance(each, IndexedPiece))
        for piece_sett in test_wc._settings:
            self.assertEqual(3, len(piece_sett))
            for sett in ['offset interval', 'voice combinations']:
                self.assertEqual(None, piece_sett[sett])
            for sett in ['filter repeats']:
                self.assertEqual(False, piece_sett[sett])
        exp_sh_setts = {'n': 2, 'continuer': 'dynamic quality', 'mark singles': False,
                        'interval quality': False, 'simple intervals': False,
                        'include rests': False, 'count frequency': True}
        self.assertEqual(exp_sh_setts, test_wc._shared_settings)
        self.assertTrue(os.path.exists(test_wc._R_bar_chart_path))

    def test_init_4(self):
        # with mostly basestrings but a few ints
        in_val = ['help.txt', 'path.xml', 4, 'why_you_do_this.rtf']
        test_wc = WorkflowManager(in_val)
        self.assertEqual(3, len(test_wc._data))
        for each in test_wc._data:
            self.assertTrue(isinstance(each, IndexedPiece))
        for piece_sett in test_wc._settings:
            self.assertEqual(3, len(piece_sett))
            for sett in ['offset interval', 'voice combinations']:
                self.assertEqual(None, piece_sett[sett])
            for sett in ['filter repeats']:
                self.assertEqual(False, piece_sett[sett])
        exp_sh_setts = {'n': 2, 'continuer': 'dynamic quality', 'mark singles': False,
                        'interval quality': False, 'simple intervals': False,
                        'include rests': False, 'count frequency': True}
        self.assertEqual(exp_sh_setts, test_wc._shared_settings)

    def test_load_1(self):
        # that "get_data" is called correctly on each thing
        test_wc = WorkflowManager([])
        test_wc._data = [mock.MagicMock(spec=IndexedPiece) for _ in xrange(5)]
        test_wc.load('pieces')
        for mock_piece in test_wc._data:
            mock_piece.get_data.assert_called_once_with([noterest.NoteRestIndexer])
        self.assertTrue(test_wc._loaded)

    def test_load_2(self):
        # that the not-yet-implemented instructions raise NotImplementedError
        test_wc = WorkflowManager([])
        self.assertRaises(NotImplementedError, test_wc.load, 'hdf5')
        self.assertRaises(NotImplementedError, test_wc.load, 'stata')
        self.assertRaises(NotImplementedError, test_wc.load, 'pickle')

    def test_load_3(self):
        # NB: this is more of an integration test
        test_wc = WorkflowManager([os.path.join(VIS_PATH, 'tests', 'corpus', 'try_opus.krn')])
        test_wc.load('pieces')
        self.assertEqual(3, len(test_wc))
        # NOTE: we have to do this by digging until music21 imports metadata from **kern files, at
        #       which point we'll be able to use our very own metadata() method
        exp_names = ['Alex', 'Sarah', 'Emerald']
        for i in xrange(3):
            # first Score gets some extra metadata
            which_el = 5 if i == 0 else 3
            piece = test_wc._data[i]._import_score()
            self.assertTrue(isinstance(piece[which_el], GlobalReference))
            self.assertEqual('COM', piece[which_el].code)
            self.assertEqual(exp_names[i], piece[which_el].value)
        # NOTE: once music21 works:
        #exp_names = ['Alex', 'Sarah', 'Emerald']
        #for i in xrange(3):
            #self.assertEqual(exp_names[i], test_wc.metadata(i, 'composer'))

    def test_load_4(self):
        # that incorrect instructions cause load() to raise a RuntimeError
        test_wc = WorkflowManager([])
        self.assertRaises(RuntimeError, test_wc.load, 'piece')
        self.assertRaises(RuntimeError, test_wc.load, 'all the data')
        self.assertRaises(RuntimeError, test_wc.load, 'not sure why I wanted three of these')

    def test_run_1(self):
        # properly deals with "intervals" experiment
        # also tests that the user can pass a custom string to the continuer setting
        mock_path = 'vis.workflow.WorkflowManager._intervs'
        with mock.patch(mock_path) as mock_meth:
            mock_meth.return_value = 'the final countdown'
            test_wc = WorkflowManager([])
            test_wc._loaded = True
            test_wc.settings(None, 'continuer', 'Unisonus')
            test_wc.run('intervals')
            mock_meth.assert_called_once_with()
            self.assertEqual(mock_meth.return_value, test_wc._result)
            self.assertEqual('intervals', test_wc._previous_exp)
            self.assertEqual('Unisonus', test_wc.settings(None, 'continuer'))

    def test_run_2a(self):
        # properly deals with "interval n-grams" experiment
        # checks that the continuer returns to 'dynamic quality' after runtime when
        # interval quality was set to True
        mock_path = 'vis.workflow.WorkflowManager._interval_ngrams'
        with mock.patch(mock_path) as mock_meth:
            mock_meth.return_value = 'the final countdown'
            test_wc = WorkflowManager([])
            test_wc._loaded = True
            test_wc.settings(None, 'interval quality', True)
            def the_side_effect():
                assert 'P1' == test_wc.settings(None, 'continuer')
                return mock.DEFAULT
            mock_meth.side_effect = the_side_effect
            test_wc.run('interval n-grams')
            mock_meth.assert_called_once_with()
            self.assertEqual(mock_meth.return_value, test_wc._result)
            self.assertEqual('interval n-grams', test_wc._previous_exp)
            self.assertEqual('dynamic quality', test_wc.settings(None, 'continuer'))

    def test_run_2b(self):
        # same as 2a but 'interval quality' is set to False
        mock_path = 'vis.workflow.WorkflowManager._interval_ngrams'
        with mock.patch(mock_path) as mock_meth:
            mock_meth.return_value = 'the final countdown'
            test_wc = WorkflowManager([])
            test_wc._loaded = True
            test_wc.settings(None, 'interval quality', False)
            def the_side_effect():
                assert '1' == test_wc.settings(None, 'continuer')
                return mock.DEFAULT
            mock_meth.side_effect = the_side_effect
            test_wc.run('interval n-grams')
            mock_meth.assert_called_once_with()
            self.assertEqual(mock_meth.return_value, test_wc._result)
            self.assertEqual('interval n-grams', test_wc._previous_exp)
            self.assertEqual('dynamic quality', test_wc.settings(None, 'continuer'))

    def test_run_3(self):
        # raise RuntimeError with invalid instructions
        test_wc = WorkflowManager([])
        test_wc._loaded = True
        self.assertRaises(RuntimeError, test_wc.run, 'too short')
        self.assertRaises(RuntimeError, test_wc.run, 'this just is not an instruction you know')

    def test_run_4(self):
        # raise RuntimeError when load() has not been called
        test_wc = WorkflowManager([])
        test_wc._loaded = False
        self.assertRaises(RuntimeError, test_wc.run, 'intervals')

    def test_split_part_combo_1(self):
        in_val = '5,6'
        expected = (5, 6)
        actual = split_part_combo(in_val)
        self.assertSequenceEqual(expected, actual)

    def test_split_part_combo_2(self):
        in_val = '234522,98100'
        expected = (234522, 98100)
        actual = split_part_combo(in_val)
        self.assertSequenceEqual(expected, actual)


class Output(TestCase):
    """Tests for WorkflowManager.output()"""

    @mock.patch('vis.workflow.WorkflowManager._make_histogram')
    def test_output_1a(self, mock_histo):
        """ensure output() calls _make_histogram() as required (with 'histogram' instruction)"""
        # 1: prepare
        histo_path = 'the_path.svg'
        mock_histo.return_value = histo_path
        test_wc = WorkflowManager([])
        test_wc._previous_exp = 'intervals'
        test_wc._data = [1 for _ in xrange(20)]
        test_wc._result = MagicMock(spec=pandas.DataFrame)
        path = 'pathname!'
        top_x = 20
        threshold = 10
        expected_args = [path, top_x, threshold]
        # 2: run
        actual = test_wc.output('histogram', path, top_x, threshold)
        # 3: check
        self.assertEqual(histo_path, actual)
        mock_histo.assert_called_once_with(*expected_args)

    @mock.patch('vis.workflow.WorkflowManager._make_histogram')
    def test_output_1b(self, mock_histo):
        """ensure output() calls _make_histogram() as required (with 'R histogram' instruction)"""
        # 1: prepare
        histo_path = 'the_path.svg'
        mock_histo.return_value = histo_path
        test_wc = WorkflowManager([])
        test_wc._previous_exp = 'intervals'
        test_wc._data = [1 for _ in xrange(20)]
        test_wc._result = MagicMock(spec=pandas.DataFrame)
        path = 'pathname!'
        top_x = 20
        threshold = 10
        expected_args = [path, top_x, threshold]
        # 2: run
        actual = test_wc.output('R histogram', path, top_x, threshold)
        # 3: check
        self.assertEqual(histo_path, actual)
        mock_histo.assert_called_once_with(*expected_args)

    @mock.patch('vis.workflow.WorkflowManager._make_lilypond')
    def test_output_2(self, mock_lily):
        """ensure output() calls _make_lilypond() as required"""
        # 1: prepare
        lily_path = 'the_path'
        mock_lily.return_value = lily_path
        test_wc = WorkflowManager([])
        test_wc._previous_exp = 'intervals'
        test_wc._data = [1 for _ in xrange(20)]
        test_wc._result = MagicMock(spec=pandas.DataFrame)
        path = 'pathname!'
        expected_args = [path]
        # 2: run
        actual = test_wc.output('LilyPond', path)
        # 3: check
        self.assertEqual(lily_path, actual)
        mock_lily.assert_called_once_with(*expected_args)

    def test_output_3(self):
        """ensure RuntimeError if there's an invalid instruction"""
        test_wc = WorkflowManager([])
        test_wc._result = [5]  # make sure that's not what causes it
        bad_instruction = 'eat dirt'
        self.assertRaises(RuntimeError, test_wc.output, bad_instruction)
        try:
            test_wc.output(bad_instruction)
        except RuntimeError as run_err:
            self.assertEqual(WorkflowManager._UNRECOGNIZED_INSTRUCTION.format(bad_instruction),
                             run_err.message)

    def test_output_4(self):
        """ensure RuntimeError if self._result is None"""
        test_wc = WorkflowManager([])
        test_wc._result = None  # just in case
        self.assertRaises(RuntimeError, test_wc.output, 'R histogram')
        try:
            test_wc.output('R histogram')
        except RuntimeError as run_err:
            self.assertEqual(WorkflowManager._NO_RESULTS_ERROR, run_err.message)

    @mock.patch('vis.workflow.WorkflowManager.export')
    def test_output_5(self, mock_export):
        """ensure output() calls export() as required"""
        # 1: prepare
        export_path = 'the_path'
        mock_export.return_value = export_path
        test_wc = WorkflowManager([])
        test_wc._previous_exp = 'intervals'
        test_wc._data = [1 for _ in xrange(20)]
        test_wc._result = MagicMock(spec=pandas.DataFrame)
        path = 'pathname!'
        expected_args = ['Excel', path, None, None]
        # 2: run
        actual = test_wc.output('Excel', path)
        # 3: check
        self.assertEqual(export_path, actual)
        mock_export.assert_called_once_with(*expected_args)


@mock.patch('vis.workflow.WorkflowManager._filter_dataframe')
@mock.patch('vis.workflow.barchart')
class MakeHistogram(TestCase):
    def test_histogram_1(self, mock_bar, mock_fdf):
        """
        That _make_histogram() works properly.
        - pathname: None
        - top_x: None
        - threshold: None
        - test_wc._previous_exp: 'intervals'
        """
        test_wc = WorkflowManager([])
        test_wc._previous_exp = 'intervals'
        mock_fdf.return_value = 'filtered DataFrame'
        exp_setts = {'pathname': 'test_output/output_result', 'token': 'interval', 'type': 'png',
                     'nr_pieces': 0}
        exp_png_path = 'your png path'
        mock_experimenter = mock.MagicMock()
        mock_experimenter.run = mock.MagicMock(return_value=exp_png_path)
        mock_bar.RBarChart = mock.MagicMock(return_value=mock_experimenter)

        actual = test_wc._make_histogram()

        self.assertEqual(exp_png_path, actual)
        mock_fdf.assert_called_once_with(top_x=None, threshold=None, name='freq')
        mock_bar.RBarChart.assert_called_once_with(mock_fdf.return_value, exp_setts)

    def test_histogram_2(self, mock_bar, mock_fdf):
        """
        That _make_histogram() works properly.
        - pathname: given
        - top_x: given
        - threshold: given
        - test_wc._previous_exp: 'n-grams'
        """
        test_wc = WorkflowManager([])
        test_wc._previous_exp = 'n-grams'
        test_wc.settings(None, 'n', 42)
        mock_fdf.return_value = 'filtered DataFrame'
        exp_setts = {'pathname': 'some_path', 'token': '42-gram', 'type': 'png',
                     'nr_pieces': 0}
        exp_png_path = 'your png path'
        mock_experimenter = mock.MagicMock()
        mock_experimenter.run = mock.MagicMock(return_value=exp_png_path)
        mock_bar.RBarChart = mock.MagicMock(return_value=mock_experimenter)

        actual = test_wc._make_histogram('some_path', 10, 100)

        self.assertEqual(exp_png_path, actual)
        mock_fdf.assert_called_once_with(top_x=10, threshold=100, name='freq')
        mock_bar.RBarChart.assert_called_once_with(mock_fdf.return_value, exp_setts)

    def test_histogram_3(self, mock_bar, mock_fdf):
        """
        That _make_histogram() works properly.
        - pathname: None
        - top_x: None
        - threshold: None
        - test_wc._previous_exp: 'cheese'
        """
        test_wc = WorkflowManager([])
        test_wc._previous_exp = 'cheese'
        mock_fdf.return_value = 'filtered DataFrame'
        exp_setts = {'pathname': 'test_output/output_result', 'token': 'objects', 'type': 'png',
                     'nr_pieces': 0}
        exp_png_path = 'your png path'
        mock_experimenter = mock.MagicMock()
        mock_experimenter.run = mock.MagicMock(return_value=exp_png_path)
        mock_bar.RBarChart = mock.MagicMock(return_value=mock_experimenter)

        actual = test_wc._make_histogram()

        self.assertEqual(exp_png_path, actual)
        mock_fdf.assert_called_once_with(top_x=None, threshold=None, name='freq')
        mock_bar.RBarChart.assert_called_once_with(mock_fdf.return_value, exp_setts)


class MakeLilyPond(TestCase):
    def test_lilypond_1a(self):
        # error conditions: if 'count frequency' is True (but the lengths are okay)
        test_wm = WorkflowManager(['fake piece'])
        test_wm._data = ['fake IndexedPiece']
        test_wm._result = ['fake results']
        # test twice like this to make sure (1) the try/except will definitely catch something, and
        # (2) we're not getting hit by another RuntimeError, of which there could be many
        self.assertRaises(RuntimeError, test_wm._make_lilypond, ['paths'])
        try:
            test_wm._make_lilypond(['paths'])
        except RuntimeError as the_err:
            self.assertEqual(WorkflowManager._COUNT_FREQUENCY_MESSAGE, the_err.message)

    def test_lilypond_1b(self):
        # error conditions: if the lengths are different, (but 'count frequency' is okay)
        test_wm = WorkflowManager(['fake piece'])
        test_wm._data = ['fake IndexedPiece']
        test_wm._result = ['fake results', 'more fake results', 'so many fake results']
        test_wm.settings(None, 'count frequency', False)
        self.assertRaises(RuntimeError, test_wm._make_lilypond, ['paths'])
        try:
            test_wm._make_lilypond(['paths'])
        except RuntimeError as the_err:
            self.assertEqual(WorkflowManager._COUNT_FREQUENCY_MESSAGE, the_err.message)

    @mock.patch('vis.models.indexed_piece.IndexedPiece', spec_set=IndexedPiece)
    def test_lilypond_2(self, test_ip):
        # make sure it works correctly with one piece that has one part
        # ("voice combinations" with literal_eval())
        # 1: prepare
        input_path = 'carpathia'
        get_data_ret = lambda *x: ['** ' + str(x[1]) if len(x) == 2 else '** ' + str(x[2][0][-3:])]
        num_parts = 1  # how many parts per piece?
        piece_list = ['test_piece.mei']
        test_wm = WorkflowManager(piece_list)
        for i in xrange(len(piece_list)):
            test_wm._data[i] = mock.MagicMock(spec_set=IndexedPiece)
            test_wm._data[i].get_data.side_effect = get_data_ret
        # the results will be like this: [['fake result 0-0', 'fake result 0-1'],
        #                                 ['fake result 1-0', 'fake result 1-1']]
        exp_results = [['fake result ' + str(i) + '-' + str(j) for j in xrange(num_parts)] \
                       for i in xrange(len(piece_list))]
        test_wm._result = exp_results
        test_wm.settings(None, 'count frequency', False)
        test_wm.settings(0, 'voice combinations', '[[0]]')
        #exp_part_labels = [{'part_names': [[0]]}]
        # 2: run
        test_wm._make_lilypond(input_path)
        # 3: check
        self.assertEqual(len(piece_list), test_ip.call_count)  # even though we don't use them
        lily_ind_list = [lilypond.AnnotationIndexer,
                         lilypond.AnnotateTheNoteIndexer,
                         lilypond.PartNotesIndexer]
        for i, piece in enumerate(test_wm._data):
            self.assertEqual(num_parts + 1, piece.get_data.call_count)
            for j in xrange(num_parts):
                piece.get_data.assert_any_call(lily_ind_list,
                                               None,  # {'part_names': exp_part_labels[i]},
                                               [exp_results[i][j]])
            sett_dict = {'run_lilypond': True,
                         'output_pathname': input_path + '.ly',
                         'annotation_part': [get_data_ret(0, 0, [z])[0] for z in exp_results[i]]}
            piece.get_data.assert_any_call([lilypond.LilyPondIndexer], sett_dict)

    @mock.patch('vis.models.indexed_piece.IndexedPiece', spec_set=IndexedPiece)
    @mock.patch('vis.workflow.WorkflowManager.metadata')
    def test_lilypond_3(self, mock_metadata, test_ip):
        # make sure it works correctly with one piece that has three parts
        # ("voice combinations" is "all pairs")
        # 1: prepare
        input_path = 'carpathia'
        get_data_ret = lambda *x: ['** ' + str(x[1]) if len(x) == 2 else '** ' + str(x[2][0][-3:])]
        num_parts = 3  # how many parts per piece? -- NB: different from previous test
        piece_list = ['test_piece.mei']
        test_wm = WorkflowManager(piece_list)
        for i in xrange(len(piece_list)):
            test_wm._data[i] = mock.MagicMock(spec_set=IndexedPiece)
            test_wm._data[i].get_data.side_effect = get_data_ret
        mock_metadata.return_value = ['part %i' % x for x in xrange(num_parts)]
        # the results will be like this: [['fake result 0-0', 'fake result 0-1'],
        #                                 ['fake result 1-0', 'fake result 1-1']]
        exp_results = [['fake result ' + str(i) + '-' + str(j) for j in xrange(num_parts)] \
                       for i in xrange(len(piece_list))]
        test_wm._result = exp_results
        test_wm.settings(None, 'count frequency', False)
        test_wm.settings(0, 'voice combinations', 'all pairs')
        #exp_part_labels = [[[0, 1], [0, 2], [1, 2]]]
        # 2: run
        test_wm._make_lilypond(input_path)
        # 3: check
        self.assertEqual(len(piece_list), test_ip.call_count)  # even though we don't use them
        lily_ind_list = [lilypond.AnnotationIndexer,
                         lilypond.AnnotateTheNoteIndexer,
                         lilypond.PartNotesIndexer]
        for i, piece in enumerate(test_wm._data):
            self.assertEqual(num_parts + 1, piece.get_data.call_count)
            for j in xrange(num_parts):
                piece.get_data.assert_any_call(lily_ind_list,
                                               None,  # {'part_names': exp_part_labels[i]},
                                               [exp_results[i][j]])
            sett_dict = {'run_lilypond': True,
                         'output_pathname': input_path + '.ly',
                         'annotation_part': [get_data_ret(0, 0, [z])[0] for z in exp_results[i]]}
            piece.get_data.assert_any_call([lilypond.LilyPondIndexer], sett_dict)

    @mock.patch('vis.models.indexed_piece.IndexedPiece', spec_set=IndexedPiece)
    @mock.patch('vis.workflow.WorkflowManager.metadata')
    def test_lilypond_4(self, mock_metadata, test_ip):
        # make sure it works correctly with three pieces that have three parts
        # ("voice combinations" is "all")
        # 1: prepare
        input_path = 'carpathia'
        get_data_ret = lambda *x: ['** ' + str(x[1]) if len(x) == 2 else '** ' + str(x[2][0][-3:])]
        num_parts = 3  # how many parts per piece? -- NB: diffferent from first test
        piece_list = ['test_piece_1.mei', 'test_piece_2.mei', 'test_piece_3.mei']
        test_wm = WorkflowManager(piece_list)
        for i in xrange(len(piece_list)):
            test_wm._data[i] = mock.MagicMock(spec_set=IndexedPiece)
            test_wm._data[i].get_data.side_effect = get_data_ret
        mock_metadata.return_value = ['part %i' % x for x in xrange(num_parts)]
        # the results will be like this: [['fake result 0-0', 'fake result 0-1'],
        #                                 ['fake result 1-0', 'fake result 1-1']]
        exp_results = [['fake result ' + str(i) + '-' + str(j) for j in xrange(num_parts)] \
                       for i in xrange(len(piece_list))]
        test_wm._result = exp_results
        test_wm.settings(None, 'count frequency', False)
        test_wm.settings(0, 'voice combinations', 'all')
        test_wm.settings(1, 'voice combinations', 'all')
        test_wm.settings(2, 'voice combinations', 'all')
        #exp_part_labels = [[[0, 2], [1, 2]] for _ in xrange(len(piece_list))]
        # 2: run
        test_wm._make_lilypond(input_path)
        # 3: check
        self.assertEqual(len(piece_list), test_ip.call_count)  # even though we don't use them
        lily_ind_list = [lilypond.AnnotationIndexer,
                         lilypond.AnnotateTheNoteIndexer,
                         lilypond.PartNotesIndexer]
        for i, piece in enumerate(test_wm._data):
            self.assertEqual(num_parts + 1, piece.get_data.call_count)
            for j in xrange(num_parts):
                piece.get_data.assert_any_call(lily_ind_list,
                                               None,  # {'part_names': exp_part_labels[j]},
                                               [exp_results[i][j]])
            # NB: the output_pathname is different from the previous two tests
            sett_dict = {'run_lilypond': True,
                        'output_pathname': input_path + '-' + str(i) + '.ly',
                        'annotation_part': [get_data_ret(0, 0, [z])[0] for z in exp_results[i]]}
            piece.get_data.assert_any_call([lilypond.LilyPondIndexer], sett_dict)


class Settings(TestCase):
    @mock.patch('vis.models.indexed_piece.IndexedPiece')
    def test_settings_1(self, mock_ip):
        # - if index is None and value are None, raise ValueError
        test_wm = WorkflowManager(['a', 'b', 'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        self.assertRaises(ValueError, test_wm.settings, None, 'filter repeats', None)
        self.assertRaises(ValueError, test_wm.settings, None, 'filter repeats')

    @mock.patch('vis.models.indexed_piece.IndexedPiece')
    def test_settings_2(self, mock_ip):
        # - if index is None, field and value are valid, it'll set for all IPs
        test_wm = WorkflowManager(['a', 'b', 'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        test_wm.settings(None, 'filter repeats', True)
        for i in xrange(3):
            self.assertEqual(True, test_wm._settings[i]['filter repeats'])

    @mock.patch('vis.models.indexed_piece.IndexedPiece')
    def test_settings_3(self, mock_ip):
        # - if index is less than 0 or greater-than-valid, raise IndexError
        test_wm = WorkflowManager(['a', 'b', 'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        self.assertRaises(IndexError, test_wm.settings, -1, 'filter repeats')
        self.assertRaises(IndexError, test_wm.settings, 20, 'filter repeats')

    @mock.patch('vis.models.indexed_piece.IndexedPiece')
    def test_settings_4(self, mock_ip):
        # - if index is 0, return proper setting
        test_wm = WorkflowManager(['a', 'b', 'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        test_wm._settings[0]['filter repeats'] = 'cheese'
        self.assertEqual('cheese', test_wm.settings(0, 'filter repeats'))

    @mock.patch('vis.models.indexed_piece.IndexedPiece')
    def test_settings_5(self, mock_ip):
        # - if index is greater than 0 but valid, set proper setting
        test_wm = WorkflowManager(['a', 'b', 'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        test_wm.settings(1, 'filter repeats', 'leeks')
        self.assertEqual('leeks', test_wm._settings[1]['filter repeats'])

    @mock.patch('vis.models.indexed_piece.IndexedPiece')
    def test_settings_6(self, mock_ip):
        # - if index is valid but the setting isn't, raise AttributeError (with or without a value)
        test_wm = WorkflowManager(['a', 'b', 'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        self.assertRaises(AttributeError, test_wm.settings, 1, 'drink wine')
        self.assertRaises(AttributeError, test_wm.settings, 1, 'drink wine', True)

    @mock.patch('vis.models.indexed_piece.IndexedPiece')
    def test_settings_7(self, mock_ip):
        # - we can properly fetch a "shared setting"
        test_wm = WorkflowManager(['a', 'b', 'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        test_wm._shared_settings['n'] = 4000
        self.assertEqual(4000, test_wm.settings(None, 'n'))

    @mock.patch('vis.models.indexed_piece.IndexedPiece')
    def test_settings_8(self, mock_ip):
        # - we can properly set a "shared setting"
        test_wm = WorkflowManager(['a', 'b', 'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        test_wm.settings(None, 'n', 4000)
        self.assertEqual(4000, test_wm._shared_settings['n'])

    @mock.patch('vis.models.indexed_piece.IndexedPiece')
    def test_settings_9(self, mock_ip):
        # - if trying to set 'offset interval' to 0, it should actually be set to None
        test_wm = WorkflowManager(['a', 'b', 'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        # "None" is default value, so first set to non-zero
        test_wm.settings(1, 'offset interval', 4.0)
        self.assertEqual(4.0, test_wm._settings[1]['offset interval'])
        # now run our test
        test_wm.settings(1, 'offset interval', 0)
        self.assertEqual(None, test_wm._settings[1]['offset interval'])


class ExtraPairs(TestCase):
    """Tests for WorkflowManager._remove_extra_pairs()"""

    def test_extra_pairs_1(self):
        """when only desired pairs are present"""
        vert_ints = DataFrame([Series([1]), Series([2]), Series([3])],
                              index=[['intervals', 'intervals', 'intervals'], ['0,1', '0,2', '1,2']]).T
        combos = ('0,1', '0,2', '1,2')
        expected = DataFrame([Series([1]), Series([2]), Series([3])],
                             index=[['intervals', 'intervals', 'intervals'], ['0,1', '0,2', '1,2']]).T
        actual = WorkflowManager._remove_extra_pairs(vert_ints, combos, 'intervals')
        self.assertSequenceEqual(list(expected.columns), list(actual.columns))

    def test_extra_pairs_2(self):
        """when no pairs are desired"""
        vert_ints = DataFrame([Series([1]), Series([2]), Series([3])],
                              index=[['intervals', 'intervals', 'intervals'], ['0,1', '0,2', '1,2']]).T
        combos = []
        expected = DataFrame()
        actual = WorkflowManager._remove_extra_pairs(vert_ints, combos, 'intervals')
        self.assertSequenceEqual(list(expected.columns), list(actual.columns))

    def test_extra_pairs_3(self):
        """when there are desired pairs, but they are not present"""
        vert_ints = DataFrame([Series([1]), Series([2]), Series([3])],
                              index=[['intervals', 'intervals', 'intervals'], ['0,1', '0,2', '1,2']]).T
        combos = ('4,20', '11,12')
        expected = DataFrame()
        actual = WorkflowManager._remove_extra_pairs(vert_ints, combos, 'intervals')
        self.assertSequenceEqual(list(expected.columns), list(actual.columns))

    def test_extra_pairs_4(self):
        """when there are lots of pairs, only some of which are desired"""
        vert_ints = DataFrame([Series([1]), Series([2]), Series([3]), Series([4]), Series([5]), Series([6])],
                              index=[['intervals' for _ in xrange(6)],
                                     ['0,1', '0,2', '1,2', '256,128', '11,12', '4,20']]).T
        combos = ('0,1', '0,2', '1,2')
        expected = DataFrame([Series([1]), Series([2]), Series([3])],
                             index=[['intervals', 'intervals', 'intervals'], ['0,1', '0,2', '1,2']]).T
        actual = WorkflowManager._remove_extra_pairs(vert_ints, combos, 'intervals')
        self.assertSequenceEqual(list(expected.columns), list(actual.columns))

    def test_extra_pairs_5(self):
        """when there are lots of pairs, only some of which are desired, and there are invalid"""
        vert_ints = DataFrame([Series([1]), Series([2]), Series([3]), Series([4]), Series([5]), Series([6])],
                              index=[['intervals' for _ in xrange(6)],
                                     ['0,1', '0,2', '1,2', '256,128', '11,12', '4,20']]).T
        combos = ('0,1', '1,2,3,4,5', '0,2', '9,11,43', '1,2')
        expected = DataFrame([Series([1]), Series([2]), Series([3])],
                             index=[['intervals', 'intervals', 'intervals'], ['0,1', '0,2', '1,2']]).T
        actual = WorkflowManager._remove_extra_pairs(vert_ints, combos, 'intervals')
        self.assertSequenceEqual(list(expected.columns), list(actual.columns))


class Export(TestCase):
    def test_export_1(self):
        # --> raise RuntimeError with unrecognized output format
        test_wm = WorkflowManager([])
        test_wm._result = pandas.Series(xrange(100))
        self.assertRaises(RuntimeError, test_wm.export, 'PowerPoint')

    def test_export_2(self):
        # --> raise RuntimeError if run() hasn't been called (i.e., self._result is None)
        test_wm = WorkflowManager([])
        self.assertRaises(RuntimeError, test_wm.export, 'Excel', 'C:\autoexec.bat')

    @mock.patch('vis.workflow.WorkflowManager._get_dataframe')
    def test_export_3(self, mock_gdf):
        # --> the method works as expected for CSV, Excel, and Stata when _result is a DataFrame
        test_wm = WorkflowManager([])
        test_wm._result = mock.MagicMock(spec=pandas.DataFrame)
        test_wm.export('CSV', 'test_path')
        test_wm.export('Excel', 'test_path')
        test_wm.export('Stata', 'test_path')
        test_wm.export('HTML', 'test_path')
        test_wm._result.to_csv.assert_called_once_with('test_path.csv')
        test_wm._result.to_stata.assert_called_once_with('test_path.dta')
        test_wm._result.to_excel.assert_called_once_with('test_path.xlsx')
        test_wm._result.to_html.assert_called_once_with('test_path.html')
        self.assertEqual(0, mock_gdf.call_count)

    @mock.patch('vis.workflow.WorkflowManager._get_dataframe')
    def test_export_4(self, mock_gdf):
        # --> test_export_3() with a valid extension already on
        test_wm = WorkflowManager([])
        test_wm._result = mock.MagicMock(spec=pandas.DataFrame)
        test_wm.export('CSV', 'test_path.csv')
        test_wm.export('Excel', 'test_path.xlsx')
        test_wm.export('Stata', 'test_path.dta')
        test_wm.export('HTML', 'test_path.html')
        test_wm._result.to_csv.assert_called_once_with('test_path.csv')
        test_wm._result.to_stata.assert_called_once_with('test_path.dta')
        test_wm._result.to_excel.assert_called_once_with('test_path.xlsx')
        test_wm._result.to_html.assert_called_once_with('test_path.html')
        self.assertEqual(0, mock_gdf.call_count)

    @mock.patch('vis.workflow.WorkflowManager._get_dataframe')
    def test_export_5(self, mock_gdf):
        # --> test_export_3() with a Series that requires calling _get_dataframe()
        test_wm = WorkflowManager([])
        test_wm._result = mock.MagicMock(spec=pandas.Series)
        # CSV
        mock_gdf.return_value = MagicMock(spec=pandas.DataFrame)
        test_wm.export('CSV', 'test_path')
        mock_gdf.assert_called_once_with('data', None, None)
        mock_gdf.return_value.to_csv.assert_called_once_with('test_path.csv')
        mock_gdf.reset_mock()
        # Excel
        test_wm.export('Excel', 'test_path', 5)
        mock_gdf.assert_called_once_with('data', 5, None)
        mock_gdf.return_value.to_excel.assert_called_once_with('test_path.xlsx')
        mock_gdf.reset_mock()
        # Stata
        test_wm.export('Stata', 'test_path', 5, 10)
        mock_gdf.assert_called_once_with('data', 5, 10)
        mock_gdf.return_value.to_stata.assert_called_once_with('test_path.dta')
        mock_gdf.reset_mock()
        # HTML
        test_wm.export('HTML', 'test_path', threshold=10)
        mock_gdf.assert_called_once_with('data', None, 10)
        mock_gdf.return_value.to_html.assert_called_once_with('test_path.html')

    def test_export_6(self):
        # --> the method always outputs a DataFrame, even if self._result isn't a DF yet
        # TODO: I don't know how to test this. I want to mock DataFrame, but it also needs to pass
        #       the isinstance() test, so it can't be a MagicMock unless it's a MagicMock instance
        #       of DataFrame, which is impossible(?) because I have to patch it at
        #       vis.workflow.pandas.DataFrame
        pass


class FilterDataFrame(TestCase):
    """Tests for WorkflowManager._filter_dataframe()"""

    def test_filter_dataframe_1(self):
        """test with top_x=auto, threshold=auto, name=auto"""
        test_wc = WorkflowManager([])
        test_wc._result = pandas.DataFrame({'data': pandas.Series([i for i in xrange(10, 0, -1)])})
        expected = pandas.DataFrame({'data': pandas.Series([i for i in xrange(10, 0, -1)])})
        actual = test_wc._filter_dataframe()
        self.assertEqual(len(expected.columns), len(actual.columns))
        for i in expected.columns:
            self.assertSequenceEqual(list(expected[i].index), list(actual[i].index))
            self.assertSequenceEqual(list(expected[i].values), list(actual[i].values))

    def test_filter_dataframe_2(self):
        """test with top_x=3, threshold=auto, name='asdf'"""
        test_wc = WorkflowManager([])
        test_wc._result = pandas.DataFrame({'asdf': pandas.Series([i for i in xrange(10, 0, -1)])})
        expected = pandas.DataFrame({'asdf': pandas.Series([10, 9, 8])})
        actual = test_wc._filter_dataframe(top_x=3, name='asdf')
        self.assertEqual(len(expected.columns), len(actual.columns))
        for i in expected.columns:
            self.assertSequenceEqual(list(expected[i].index), list(actual[i].index))
            self.assertSequenceEqual(list(expected[i].values), list(actual[i].values))

    def test_filter_dataframe_3(self):
        """test with top_x=3, threshold=5 (so the top_x still removes after threshold), name=auto"""
        test_wc = WorkflowManager([])
        test_wc._result = pandas.DataFrame({'data': pandas.Series([i for i in xrange(10, 0, -1)])})
        expected = pandas.DataFrame({'data': pandas.Series([10, 9, 8])})
        actual = test_wc._filter_dataframe(top_x=3, threshold=5)
        self.assertEqual(len(expected.columns), len(actual.columns))
        for i in expected.columns:
            self.assertSequenceEqual(list(expected[i].index), list(actual[i].index))
            self.assertSequenceEqual(list(expected[i].values), list(actual[i].values))

    def test_filter_dataframe_4(self):
        """test with top_x=5, threshold=7 (so threshold leaves fewer than 5 results), name=auto"""
        test_wc = WorkflowManager([])
        test_wc._result = pandas.DataFrame({'data': pandas.Series([i for i in xrange(10, 0, -1)])})
        expected = pandas.DataFrame({'data': pandas.Series([10, 9, 8])})
        actual = test_wc._filter_dataframe(top_x=5, threshold=7)
        self.assertEqual(len(expected.columns), len(actual.columns))
        for i in expected.columns:
            self.assertSequenceEqual(list(expected[i].index), list(actual[i].index))
            self.assertSequenceEqual(list(expected[i].values), list(actual[i].values))

    def test_filter_dataframe_5(self):
        """test with top_x=3, threshold=auto, name='asdf'; many input columns"""
        test_wc = WorkflowManager([])
        test_wc._result = pandas.DataFrame({('1', 'b'): pandas.Series([i for i in xrange(10, 0, -1)]),
                                            ('1', 'z'): pandas.Series([i for i in xrange(10, 20)]),
                                            ('2', 'e'): pandas.Series([i for i in xrange(40, 900)])})
        expected = pandas.DataFrame({'asdf': pandas.Series([10, 9, 8])})
        actual = test_wc._filter_dataframe(top_x=3, name='asdf')
        self.assertEqual(len(expected.columns), len(actual.columns))
        for i in expected.columns:
            self.assertSequenceEqual(list(expected[i].index), list(actual[i].index))
            self.assertSequenceEqual(list(expected[i].values), list(actual[i].values))

    def test_filter_dataframe_6(self):
        """test with top_x=3, threshold=auto, name=auto; many input columns"""
        test_wc = WorkflowManager([])
        test_wc._result = pandas.DataFrame({('1', 'b'): pandas.Series([i for i in xrange(10, 0, -1)]),
                                            ('1', 'z'): pandas.Series([i for i in xrange(10, 20)]),
                                            ('2', 'e'): pandas.Series([i for i in xrange(40, 900)])})
        expected = pandas.DataFrame({('1', 'b'): pandas.Series([10, 9, 8]),
                                     ('1', 'z'): pandas.Series([10, 11, 12]),
                                     ('2', 'e'): pandas.Series([40, 41, 42])})
        actual = test_wc._filter_dataframe(top_x=3)
        self.assertEqual(len(expected.columns), len(actual.columns))
        for i in expected.columns:
            self.assertSequenceEqual(list(expected[i].index), list(actual[i].index))
            self.assertSequenceEqual(list(expected[i].values), list(actual[i].values))


class AuxiliaryExperimentMethods(TestCase):
    """Tests for auxiliary methods used by some experiments."""

    @mock.patch('vis.workflow.repeat.FilterByRepeatIndexer')
    @mock.patch('vis.workflow.offset.FilterByOffsetIndexer')
    def test_run_off_rep_1(self, mock_off, mock_rep):
        """run neither indexer"""
        # setup
        workm = WorkflowManager(['', '', ''])
        workm._data = [None, MagicMock(spec=IndexedPiece), None]
        workm.settings(1, 'offset interval', 0)
        workm.settings(1, 'filter repeats', False)
        in_val = 42
        # run
        actual = workm._run_off_rep(1, in_val)
        # test
        self.assertEqual(in_val, actual)
        self.assertEqual(0, workm._data[1].get_data.call_count)

    @mock.patch('vis.workflow.repeat.FilterByRepeatIndexer')
    @mock.patch('vis.workflow.offset.FilterByOffsetIndexer')
    def test_run_off_rep_2(self, mock_off, mock_rep):
        """run offset indexer"""
        # setup
        workm = WorkflowManager(['', '', ''])
        workm._data = [None, MagicMock(spec=IndexedPiece), None]
        workm._data[1].get_data.return_value = 24
        workm.settings(1, 'offset interval', 0.5)
        workm.settings(1, 'filter repeats', False)
        in_val = 42
        # run
        actual = workm._run_off_rep(1, in_val)
        # test
        self.assertEqual(workm._data[1].get_data.return_value, actual)
        workm._data[1].get_data.assert_called_once_with([mock_off], {'quarterLength': 0.5}, in_val)

    @mock.patch('vis.workflow.repeat.FilterByRepeatIndexer')
    @mock.patch('vis.workflow.offset.FilterByOffsetIndexer')
    def test_run_off_rep_3(self, mock_off, mock_rep):
        """run repeat indexer"""
        # setup
        workm = WorkflowManager(['', '', ''])
        workm._data = [None, MagicMock(spec=IndexedPiece), None]
        workm._data[1].get_data.return_value = 24
        workm.settings(1, 'offset interval', 0)
        workm.settings(1, 'filter repeats', True)
        in_val = 42
        # run
        actual = workm._run_off_rep(1, in_val)
        # test
        self.assertEqual(workm._data[1].get_data.return_value, actual)
        workm._data[1].get_data.assert_called_once_with([mock_rep], {}, in_val)

    @mock.patch('vis.workflow.repeat.FilterByRepeatIndexer')
    @mock.patch('vis.workflow.offset.FilterByOffsetIndexer')
    def test_run_off_rep_4(self, mock_off, mock_rep):
        """run offset and repeat indexer"""
        # setup
        workm = WorkflowManager(['', '', ''])
        workm._data = [None, MagicMock(spec=IndexedPiece), None]
        workm._data[1].get_data.return_value = 24
        workm.settings(1, 'offset interval', 0.5)
        workm.settings(1, 'filter repeats', True)
        in_val = 42
        # run
        actual = workm._run_off_rep(1, in_val)
        # test
        self.assertEqual(workm._data[1].get_data.return_value, actual)
        self.assertEqual(2, workm._data[1].get_data.call_count)
        workm._data[1].get_data.assert_any_call([mock_off], {'quarterLength': 0.5}, in_val)
        workm._data[1].get_data.assert_any_call([mock_rep], {}, workm._data[1].get_data.return_value)

    @mock.patch('vis.workflow.repeat.FilterByRepeatIndexer')
    @mock.patch('vis.workflow.offset.FilterByOffsetIndexer')
    def test_run_off_rep_5(self, mock_off, mock_rep):
        """run offset indexer with is_horizontal set to True"""
        # setup
        workm = WorkflowManager(['', '', ''])
        workm._data = [None, MagicMock(spec=IndexedPiece), None]
        workm._data[1].get_data.return_value = 24
        workm.settings(1, 'offset interval', 0.5)
        workm.settings(1, 'filter repeats', False)
        in_val = 42
        # run
        actual = workm._run_off_rep(1, in_val, True)
        # test
        self.assertEqual(workm._data[1].get_data.return_value, actual)
        workm._data[1].get_data.assert_called_once_with([mock_off],
                                                        {'quarterLength': 0.5, 'method': None},
                                                        in_val)

#-------------------------------------------------------------------------------------------------#
# Definitions                                                                                     #
#-------------------------------------------------------------------------------------------------#
WORKFLOW_TESTS = TestLoader().loadTestsFromTestCase(WorkflowTests)
FILTER_DATA_FRAME = TestLoader().loadTestsFromTestCase(FilterDataFrame)
EXPORT = TestLoader().loadTestsFromTestCase(Export)
EXTRA_PAIRS = TestLoader().loadTestsFromTestCase(ExtraPairs)
SETTINGS = TestLoader().loadTestsFromTestCase(Settings)
OUTPUT = TestLoader().loadTestsFromTestCase(Output)
AUX_METHODS = TestLoader().loadTestsFromTestCase(AuxiliaryExperimentMethods)
MAKE_HISTOGRAM = TestLoader().loadTestsFromTestCase(MakeHistogram)
MAKE_LILYPOND = TestLoader().loadTestsFromTestCase(MakeLilyPond)
