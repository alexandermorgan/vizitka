#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           vis
# Program Description:    Helps analyze music with computers.
#
# Filename:               controllers/workflow.py
# Purpose:                Workflow Controller
#
# Copyright (C) 2013 Christopher Antila
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
Workflow controller, to automate commonly-performed tasks.
"""

import subprocess
import pandas
from vis.models import indexed_piece
from vis.models.aggregated_pieces import AggregatedPieces
from vis.analyzers.indexers import noterest, interval, ngram
from vis.analyzers.experimenters import frequency, aggregator


class WorkflowManager(object):
    """
    The :class:`WorkflowManager` automates several commonly-performed music analysis patterns.

    There are four basic tasks the :class:`WorkflowManager` performs, each with its own method:

    * :meth:`load`, to import data from external formats (MusicXML, Stata, pickled, etc.).
    * :meth:`run`, which performs one of a small set of pre-defined analysis activities.
    * :meth:`output`, which outputs visualization data to disk.
    * :meth:`export`, which outputs "non-visual" data to disk (Stata, CSV, pickled, etc.)

    We also provide the following methods for setting and getting properties of the individual
    :class:`~vis.models.indexed_piece.IndexedPiece` objects:

    * :meth:`metadata`, to adjust or view the metadata of a piece.
    * :meth:`settings`, to adjust or view the settings of a piece.
    """
    # TODO: pay attention to voice-combination settings for finding interval n-grams

    # Instance Variables
    # - self._data = list of IndexedPieces
    # - self._result = result of the most recent call to run()

    def __init__(self, vals):
        """
        It's often easier to use the :class:`WorkflowManager`, by providing a list of pathnames \
        corresponding to the files you want to analyze. However, if you will later need access to \
        the :class:`~vis.models.indexed_piece.IndexedPiece` objects directly themselves, you \
        should provide them to the :class:`WorkflowManager` as in the second example below.

        Parameters
        ==========
        :parameter vals: A list of pathnames or IndexedPieces. If an item in the list is not \
            either an IndexedPiece or basestring, it is silently ignored.
        :type vals: :obj:`list` of :obj:`basestring` or of \
            :obj:`~vis.models.indexed_piece.IndexedPiece`

        We manage the :class:`~vis.models.indexed_piece.IndexedPiece` objects:
        >>> paths = [u'test_corpus/bwv77.mxl', u'test_corpus/Kyrie.krn']
        >>> path_work = WorkflowManager(paths)

        You manage the :class:`~vis.models.indexed_piece.IndexedPiece` objects:
        >>> ips = [IndexedPiece(x) for x in paths]
        >>> ip_work = WorkflowManager(ips)
        """
        post = []
        for each_val in vals:
            if isinstance(each_val, basestring):
                post.append(indexed_piece.IndexedPiece(each_val))
            elif isinstance(each_val, indexed_piece.IndexedPiece):
                post.append(each_val)
        self._data = post
        self._result = None
        self._settings = [{} for _ in xrange(len(self._data))]
        for piece_sett in self._settings:
            for sett in [u'offset interval', u'voice combinations']:
                piece_sett[sett] = None
            for sett in [u'filter repeats', u'interval quality', u'simple intervals']:
                piece_sett[sett] = False

    def __len__(self):
        """
        Return the number of pieces stored in this WorkflowManager.
        """
        return len(self._data)

    def load(self, instruction, pathname=None):
        """
        Import analysis data from long-term storage on a filesystem. This should primarily be \
        used for the :obj:`u'pieces'` instruction, to control when the initial music21 import \
        happens.

        **Instructions:**

        .. note:: only :obj:`u'pieces'` is implemented at this time.

        * :obj:`u'pieces'`, to import all pieces, collect metadata, and run :class:`NoteRestIndexer`
        * :obj:`u'hdf5'` to load data from a previous :meth:`export`.
        * :obj:`u'stata'` to load data from a previous :meth:`export`.
        * :obj:`u'pickle'` to load data from a previous :meth:`export`.

        Parameters
        ==========
        :parameter instruction: The type of data to load.
        :type instruction: :obj:`basestring`
        :parameter pathname: The pathname of the data to import; not required for the u'pieces' \
            instruction.
        :type pathname: :obj:`basestring`
        """
        # TODO: rewrite this with multiprocessing
        # NOTE: you may want to have the worker process create a new IndexedPiece object, import it
        #       and run the NoteRestIndexer, then pickle it and send that to a callback method
        #       that will somehow unpickle it and replace the *data in* the IndexedPieces here, but
        #       not actually replace the IndexedPieces, since that would inadvertently cancel the
        #       client's pointer to the IndexedPieces, if they have one
        if u'pieces' == instruction:
            for piece in self._data:
                piece.get_data([noterest.NoteRestIndexer])
        elif u'hdf5' == instruction or u'stata' == instruction or u'pickle' == instruction:
            raise NotImplementedError(u'The ' + instruction + u' instruction does\'t work yet!')

    def run(self, instruction, settings=None):
        """
        Run a commonly-requested experiment workflow.

        Parameters
        ==========
        :parameter instruction: The experiment workflow to run.
        :type instruction: :obj:`basestring`
        :parameter settings: Settings to be shared across all experiments that will be run. Refer \
            to the relevant indexers' :obj:`possible_settings` property to know the relevant \
            settings. Default is :obj:`None`.
        :type settings: :obj:`dict`

        Returns
        =======
        :returns: The result of the experiment workflow.
        :rtype: :class:`pandas.Series` or :class:`pandas.DataFrame`

        Raises
        ======
        :raises: :exc:`RuntimeError` if the :obj:`instruction` does not make sense.

        Instructions:

        * :obj:`'all-combinations intervals'`: finds the frequency of vertical intervals in all \
            2-part voice combinations.
        * :obj:`'all 2-part interval n-grams'`: finds the frequency of 2-part vertical interval \
            n-grams in all voice pair combinations. Remember to specify the :obj:`u'n'` setting.
        * :obj:`'all-voice interval n-grams'`: finds the frequency of all-part vertical interval \
            n-grams. Remember to specify the :obj:`u'n'` setting.

        Modifiers:

        * :obj:`u' for SuperCollider'`: append this to :obj:`u'all-combinations intervals'` to \
            prepare a :class:`DataFrame` with the information required for Mike Winters' \
            sonification program. You should then call :meth:`export` with the :obj:`u'CSV'` \
            instruction.
        """
        # TODO: handle RepeatFilter
        # TODO: handle OffsetIndexer
        # NOTE: do not re-order the instructions or this method will break
        possible_instructions = [u'all-combinations intervals',
                                 u'all 2-part interval n-grams',
                                 u'all-voice interval n-grams']
        error_msg = u'WorkflowManager.run() could not parse the instruction'
        post = None
        # run the experiment
        if len(instruction) < min([len(x) for x in possible_instructions]):
            raise RuntimeError(error_msg)
        if instruction.startswith(possible_instructions[0]):
            post = self._intervs(settings)
        elif instruction.startswith(possible_instructions[1]):
            post = self._two_part_modules(settings)
        elif instruction.startswith(possible_instructions[2]):
            post = self._all_part_modules(settings)
        else:
            raise RuntimeError(error_msg)
        # format for SuperCollider, if required
        if -1 != instruction.rfind(u' for SuperCollider'):
            post = WorkflowManager._for_sc(post)
        self._result = post
        return post

    def _two_part_modules(self, settings):
        """
        Prepare a list of frequencies of two-voice interval n-grams in all pieces. These indexers \
        and experimenters will run:

        * :class:`IntervalIndexer`
        * :class:`HorizontalIntervalIndexer`
        * :class:`NGramIndexer`
        * :class:`FrequencyExperimenter`
        * :class:`ColumnAggregator`

        :parameter settings: Settings to be shared across all experiments that will be run. Refer \
            to the relevant indexers' :obj:`possible_settings` property to know the relevant \
            settings.
        :type settings: :obj:`dict`
        :returns: The result of :class:`ColumnAggregator`
        :rtype: :class:`pandas.Series`

        To compute more than one value of 'n', simply call :meth:`_two_part_modules` many times.
        """
        ngram_freqs = []
        for piece in self._data:
            vert_ints = piece.get_data([noterest.NoteRestIndexer, interval.IntervalIndexer],
                                       settings)
            horiz_ints = piece.get_data([noterest.NoteRestIndexer,
                                         interval.HorizontalIntervalIndexer],
                                        settings)
            # each key in vert_ints corresponds to a two-voice combination we should use
            for combo in vert_ints.iterkeys():
                # which "horiz" part to use?
                horiz_i = interval.key_to_tuple(combo)[1]
                # make the list of parts
                parts = [vert_ints[combo], horiz_ints[horiz_i]]
                # assemble settings
                setts = {u'vertical': [0], u'horizontal': [1]}
                if u'mark singles' in settings:
                    setts[u'mark singles'] = settings[u'mark singles']
                if u'continuer' in settings:
                    setts[u'continuer'] = settings[u'continuer']
                setts[u'n'] = settings[u'n']
                # run NGramIndexer and FrequencyExperimenter, then append the result to the
                # corresponding index of the dict
                ngram_freqs.append(piece.get_data([ngram.NGramIndexer,
                                                   frequency.FrequencyExperimenter],
                                        setts,
                                        parts))
        agg_p = AggregatedPieces(self._data)
        post = agg_p.get_data([aggregator.ColumnAggregator], None, {}, ngram_freqs)
        post.sort(ascending=False)
        return post

    def _all_part_modules(self, settings):
        """
        Prepare a list of frequencies of all-voice interval n-grams in all pieces. These indexers \
        and experimenters will run:

        * :class:`IntervalIndexer`
        * :class:`HorizontalIntervalIndexer`
        * :class:`NGramIndexer`
        * :class:`FrequencyExperimenter`
        * :class:`ColumnAggregator`

        :parameter settings: Settings to be shared across all experiments that will be run. Refer \
            to the relevant indexers' :obj:`possible_settings` property to know the relevant \
            settings.
        :type settings: :obj:`dict`
        :returns: The result of :class:`ColumnAggregator`
        :rtype: :class:`pandas.Series`

        To compute more than one value of 'n', simply call :meth:`_all_part_modules` many times.
        """
        ngram_freqs = []
        for piece in self._data:
            vert_ints = piece.get_data([noterest.NoteRestIndexer, interval.IntervalIndexer],
                                       settings)
            horiz_ints = piece.get_data([noterest.NoteRestIndexer,
                                         interval.HorizontalIntervalIndexer],
                                        settings)
            # figure out the weird string-index things for the vertical part combos
            lowest_part = len(piece.metadata(u'parts')) - 1
            vert_combos = [str(x) + u',' + str(lowest_part) for x in xrange(lowest_part)]
            # make the list of parts
            parts = [vert_ints[x] for x in vert_combos]
            parts.append(horiz_ints[-1])  # always the lowest voice
            # assemble settings
            setts = {u'vertical': range(len(parts) - 1), u'horizontal': [len(parts) - 1]}
            if u'mark singles' in settings:
                setts[u'mark singles'] = settings[u'mark singles']
            if u'continuer' in settings:
                setts[u'continuer'] = settings[u'continuer']
            setts[u'n'] = settings[u'n']
            # run NGramIndexer and FrequencyExperimenter, then append the result to the
            # corresponding index of the dict
            ngram_freqs.append(piece.get_data([ngram.NGramIndexer, frequency.FrequencyExperimenter],
                                              setts,
                                              parts))
        agg_p = AggregatedPieces(self._data)
        post = agg_p.get_data([aggregator.ColumnAggregator], None, {}, ngram_freqs)
        post.sort(ascending=False)
        return post

    def _intervs(self, settings):
        """
        Prepare a list of frequencies of intervals between all voice pairs of all pieces. These \
        indexers and experimenters will run:

        * :class:`IntervalIndexer`
        * :class:`FrequencyExperimenter`
        * :class:`ColumnAggregator`

        :parameter settings: Settings to be shared across all experiments that will be run. Refer \
            to the relevant indexers' :obj:`possible_settings` property to know the relevant \
            settings.
        :type settings: :obj:`dict`
        :returns: The result of :class:`ColumnAggregator`
        :rtype: :class:`pandas.Series`
        """
        int_freqs = []
        for piece in self._data:
            vert_ints = piece.get_data([noterest.NoteRestIndexer, interval.IntervalIndexer],
                                       settings)
            # aggregate results from all voice pairs and save for later
            int_freqs.append(piece.get_data([frequency.FrequencyExperimenter,
                                             aggregator.ColumnAggregator],
                                            {},
                                            list(vert_ints.itervalues())))
        agg_p = AggregatedPieces(self._data)
        post = agg_p.get_data([aggregator.ColumnAggregator], None, {}, int_freqs)
        post.sort(ascending=False)
        return post

    @staticmethod
    def _for_sc(to_format):
        """
        Format a record for output to the vis SuperCollider application.

        :parameter to_format: The experimental results to be formatted.
        :type to_format: ???
        :returns: The results, formatted for SuperCollider.
        :rtype: ???
        """
        pass

    def output(self, instruction, pathname=u'test_output/output_result'):
        """
        Create a visualization from the most recent result of :meth:`run` and save it to a file.

        Parameters
        ==========
        :parameter instruction: The type of visualization to output.
        :type instruction: :obj:`basestring`
        :parameter pathname: The pathname for the output. If not specified, we will choose. Do not
            provide a filename extension---this is automatic.
        :type pathname: :obj:`basestring`

        Returns
        =======
        :returns: The pathname of the outputted visualization.
        :rtype: :obj:`unicode`

        Raises
        ======
        :raises: :exc:`NotImplementedError` if you use the ``u'LilyPond'`` instruction.
        :raises: :exc:`RuntimeError` for unrecognized instructions.
        :raises: :exc:`RuntimeError` if :meth:`run` has never been called.

        **Instructions:**

        .. note:: Only the ``u'R histogram'`` instruction works at the moment.

        * :obj:`u'LilyPond'`: not yet sure what this will be like...
        * :obj:`u'R histogram'`: a histogram with ggplot2 in R.
        """
        if instruction == u'LilyPond':
            raise NotImplementedError(u'I didn\'t write that part yet!')
        elif instruction == u'R histogram':
            if self._result is None:
                raise RuntimeError(u'Call run() before calling output()')
            else:
                stata_path = pathname + u'.dta'
                png_path = pathname + u'.png'
                out_me = pandas.DataFrame({u'freq': self._result})
                out_me.to_stata(stata_path)
                call_to_r = [u'R', u'--vanilla', u'-f', u'R_script.r', u'--args', stata_path,
                             png_path]
                subprocess.call(call_to_r)
                return png_path
        else:
            raise RuntimeError(u'Unrecognized instruction: ' + unicode(instruction))

    def export(self, form, pathname=None):
        """
        Save data from the most recent result of :meth:`run` to a file.

        Parameters
        ==========
        :parameter form: The output format you want.
        :type form: :obj:`basestring`
        :parameter pathname: The pathname for output. If not specified, we will choose.
        :type pathname: :obj:`basestring`

        Returns
        =======
        :returns: The pathname of the outputted file.
        :rtype: :obj:`unicode`

        Formats:

        * :obj:`u'CSV'`: output a Series or DataFrame to a CSV file.
        * :obj:`u'HDF5'`: output a Series or DataFrame to an HDF5 file.
        * :obj:`u'pickle'`: save everything to a pickle file so we can re-load the current state \
            later (NOTE: this does not work yet)
        * :obj:`u'Stata'`: output a Stata file for importing to R.
        * :obj:`u'Excel'`: output an Excel file for Peter Schubert.
        """
        pass

    def metadata(self, index, field, value=None):
        """
        Use this method to get or set a particular metadatum. The valid field names are listed in
        IndexedPiece.:meth:`~vis.models.indexed_piece.IndexedPiece.metadata`.

        A metadatum is a salient musical characteristic of a particular piece, and does not change
        across analyses.

        :param index: The index of the piece to access. The range of valid indices is ``0`` through
            one fewer than the return value of calling :func:`len` on this WorkflowManager.
        :type index: :obj:`int`
        :param field: The name of the field to be accessed or modified.
        :type field: :obj:`basestring`
        :param value: If not ``None``, the new value to be assigned to ``field``.
        :type value: :obj:`object` or :obj:`None`

        :returns: The value of the requested field or ``None``, if assigning, or if accessing a
            non-existant field or a field that has not yet been initialized.
        :rtype: :obj:`object` or :obj:`None`

        :raises: :exc:`TypeError` if ``field`` is not a ``basestring``.
        :raises: :exc:`AttributeError` if accessing an invalid ``field`` (see valid fields below).
        :raises: :exc:`IndexError` if ``index`` is invalid for this ``WorkflowManager``.
        """
        return self._data[index].metadata(field, value)

    def settings(self, index, field, value=None):
        """
        Use this method to get or set a particular setting. The valid values are listed below.

        A setting is related to this particular analysis, and is not a salient musical feature of
        the work itself.

        :param index: The index of the piece to access. The range of valid indices is ``0`` through
            one fewer than the return value of calling :func:`len` on this WorkflowManager. If
            ``value`` is not ``None`` and ``index`` is ``None``, you can set a field for all pieces.
        :type index: :obj:`int`
        :param field: The name of the field to be accessed or modified.
        :type field: :obj:`basestring`
        :param value: If not ``None``, the new value to be assigned to ``field``.
        :type value: :obj:`object` or :obj:`None`

        :returns: The value of the requested field or ``None``, if assigning, or if accessing a
            non-existant field or a field that has not yet been initialized.
        :rtype: :obj:`object` or :obj:`None`

        :raises: :exc:`AttributeError` if accessing an invalid ``field`` (see valid fields below).
        :raises: :exc:`IndexError` if ``index`` is invalid for this ``WorkflowManager``.
        :raises: :exc:`ValueError` if ``index`` and ``value`` are both ``None``.

        **Setting Fields:**

        * ``offset interval``: If you want to run the \
            :class:`~vis.analyzers.indexers.offset.FilterByOffsetIndexer`, specify a value for this
            setting that will become the quarterLength duration between observed offsets.
        * ``filter repeats``: If you want to run the \
            :class:`~vis.analyzers.indexers.repeat.FilterByRepeatIndexer`, set this setting to \
            ``True``.
        * ``voice combinations``: If you want to consider certain specific voice combinations, \
            set this setting to a list of a list of iterables. The following value would analyze \
            the highest three voices with each other: ``[[0,1,2]]`` while this would analyze the \
            every part with the lowest for a four-part piece: ``[[0, 3], [1, 3], [2, 3]]``.
        * ``interval quality``: If you want to display interval quality, set this setting to \
            ``True``.
        * ``simple intervals``: If you want to display all intervals as their single-octave \
            equivalents, set this setting to ``True``.
        """
        if index is None:
            if value is None:
                raise ValueError(u'If "index" is None, "value" must not be None.')
            else:
                for i in xrange(len(self._settings)):
                    self.settings(i, field, value)
        elif not 0 <= index < len(self._settings):
            raise IndexError(u'Invalid inex for this WorkflowManager (' + unicode(index) + u')')
        elif field not in self._settings[index]:
            raise AttributeError(u'Invalid setting: ' + unicode(field))
        elif value is None:
            return self._settings[index][field]
        else:
            self._settings[index][field] = value
