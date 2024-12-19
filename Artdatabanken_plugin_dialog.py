# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ArtdatabankenDialog
                                 A QGIS plugin
 Getting data from Artdatabanken
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-11-20
        git sha              : $Format:%H$
        copyright            : (C) 2024 by LU
        email                : 00albabj@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from PyQt5.QtWidgets import QDialog, QCheckBox


# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Artdatabanken_plugin_dialog_base.ui'))

FIRST_POP, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'First_pop_up.ui'))

ART_TYPE, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Art_type.ui'))


WFS_INFO, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'WFS.ui'))

WFS_SEARCH, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'WFS_search.ui'))

ATT_ART, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'attribut_art.ui'))
class ArtdatabankenDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(ArtdatabankenDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.selectAll.clicked.connect(self.select_all)
        self.clearAll.clicked.connect(self.clear_all)

        # Find all checkboxes (assuming they are within a specific container)
        self.checkboxes = self.findChildren(QCheckBox)

    def select_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def clear_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

class FirstPopupDialog(QtWidgets.QDialog, FIRST_POP):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

class ArtTypeDialog(QtWidgets.QDialog, ART_TYPE):
    def __init__(self, parent=None):
        super(ArtTypeDialog, self).__init__(parent)
        self.setupUi(self)

class ArtAttDialog(QtWidgets.QDialog, ATT_ART):
    def __init__(self, parent=None):
        super(ArtAttDialog, self).__init__(parent)
        self.setupUi(self)
        self.selectAll.clicked.connect(self.select_all)
        self.clearAll.clicked.connect(self.clear_all)

        # Find all checkboxes (assuming they are within a specific container)
        self.checkboxes = self.findChildren(QCheckBox)

    def select_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def clear_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

class WFSSearchDialog(QtWidgets.QDialog, WFS_SEARCH):
    def __init__(self, parent=None):
        super(WFSSearchDialog, self).__init__(parent)
        self.setupUi(self)

        # Add start- and end-date as variables
        self.startDate = self.findChild(QtWidgets.QDateEdit, 'startDate')
        self.endDate = self.findChild(QtWidgets.QDateEdit, 'endDate')
        

class WFSInfoDialog(QtWidgets.QDialog, WFS_INFO):
    def __init__(self, parent=None):
        super(WFSInfoDialog, self).__init__(parent)
        self.setupUi(self)
        self.selectAll.clicked.connect(self.select_all)
        self.clearAll.clicked.connect(self.clear_all)

        # Find all checkboxes (assuming they are within a specific container)
        self.checkboxes = self.findChildren(QCheckBox)

    def select_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def clear_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)