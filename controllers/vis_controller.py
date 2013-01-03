#! /usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Program Name:              vis
# Program Description:       Measures sequences of vertical intervals.
#
# Filename: vis_controller.py
# Purpose: Holds the VisController objects for the various GUIs.
#
# Copyright (C) 2012 Jamie Klassen, Christopher Antila
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
'''
Holds the VisController objects for the various GUIs.
'''



# Imports from...
# PyQt4
from PyQt4.QtCore import pyqtSignal, QObject
# vis
from views.Ui_main_window import Ui_MainWindow
from models.analyzing import ListOfPieces



class VisController(Ui_MainWindow):
   '''
   Subclasses the automatically-generated python code in Ui_main_window that
   creates the GUI. Although there is a dependency on QtCore, for the PyQt
   signals-and-slots mechanism, we must try to avoid using QtGui methods as
   much as possible, so that, in the future, we can use other GUIs without
   importing Ui_main_window from the PyQt GUI.

   This class creates the GUI and manages interaction between other Controller
   subclasses and the GUI. It is effectively both the GUI's controller and the
   super-controller for Importer, Analyzer, Experimenter, and DisplayHandler,
   since VisController also "translates" GUI actions into the signals expected
   by the other controller subclasses.

   TODO: doctest
   '''
   # NOTE: We will have to rewrite most of this class when we want to implement
   # other (non-PyQt4) interfaces, but the use patterns, and maybe even the
   # algorithms, should stay mostly the same.

   # NOTE2: We may need other methods for other interfaces, but for PyQt4, we
   # only need __init__().



   def __init__(self, interface='PyQt4', details=None):
      '''
      Create a new VisController instance.

      The first argument, "interface", is a string specifying which GUI to use:
      - 'PyQt4'
      - 'HTML5' (not implemented)
      - others?

      The second argument, "details", is a list of arguments specifying settings
      to be used when creating the specific interface. So far, there are none.
      '''
      # Setup things we need to know
      self.UI_type = interface

      # Setup signals for GUI-only things

      # Create long-term sub-controllers
      # self.importer = ?
      # self.analyzer = ?
      # self.experimenter = ?
      # self.displayer = ?

      # Setup signals TO the long-term sub-controllers
      # self.importer.setup_signals()
      # self.analyzer.setup_signals()
      # self.experimenter.setup_signals()
      # self.displayer.setup_signals()

      # Setup signals FROM the long-term sub-controllers

      # Set the models for the table views.
      #self.gui_file_list.setModel(self.importer.list_of_files)
      #self.gui_pieces_list.setModel(self.analyzer.list_of_pieces)
# End class VisController ------------------------------------------------------



class VisSignals(QObject):
   '''
   The VisSignals class holds signals used for communication between
   controllers and their views. We're using signals-and-slots because it helps
   us with the MVC separation: a controller need not know *which* GUI is being
   used, so long as it knows that it will receive particular signals.
   Furthermore, there need not be a one-to-one correspondence between GUI
   widgets and methods in the models.

   Currently depends on PyQt4.QtCore.QObject for the signals-and-slots
   implementation.
   '''
   # Create a signal like this:
   # signal_name = pyqtSignal(str)

   # Importer
   importer_add_pieces = pyqtSignal(list) # a list of str filenames
   importer_remove_pieces = pyqtSignal(list) # a list of str filenames
   importer_add_remove_success = pyqtSignal(bool) # whether the add/remove operation was successful
   importer_import = pyqtSignal(str) # create a ListOfPieces from the ListOfFiles; argument ignored
   importer_imported = pyqtSignal(ListOfPieces) # the result of importer_import
   importer_error = pyqtSignal(str) # description of an error in the Importer
   importer_status = pyqtSignal(str) # informs the GUI of the status for a currently-running import (if two or three characters followed by a '%' then it should try to update a progress bar, if available)

   # Analyzer
   # TODO: figure out what type "index" and "data" are
   #analyzer_change_settings = pyqtSignal(index, data) # change the data of a cell in the ListOfPieces; the GUI will know how to create an index based on which rows are selected and which data is being changed (cross-referenced with the ListOfPieces' declaration of column indices)
   analyzer_analyze = pyqtSignal(str) # to tell the Analyzer controller to perform analysis
   analyzer_analyzed = pyqtSignal(list) # the result of analyzer_analyze; the result is a list of AnalysisRecord objects
   analyzer_error = pyqtSignal(str) # description of an error in the Analyzer
   analyzer_status = pyqtSignal(str) # informs the GUI of the status for a currently-running analysis (if two or three characters followed by a '%' then it should try to update a progress bar, if available)

   # Experimenter
   experimenter_set = pyqtSignal(tuple) # a 2-tuple: a string for a setting name and the value for the setting
   experimenter_experiment = pyqtSignal(str) # tell the Experimenter controller to perform an experiment
   experimenter_experimented = pyqtSignal(tuple) # the result of experimenter_experiment; the result is a tuple, where the first element is the type of Display object to use, and the second is whatever the Display object needs
   experimenter_error = pyqtSignal(str) # description of an error in the Experimenter
   experimenter_status = pyqtSignal(str) # informs the GUI of the status for a currently-running experiment (if two or three characters followed by a '%' then it should try to update a progress bar, if available)

   # DisplayHandler
   display_shown = pyqtSignal(str) # when the user should be able to see the results of an experiment on the screen in a particular format
# End class VisSignals ---------------------------------------------------------