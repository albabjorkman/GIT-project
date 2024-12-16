# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Artdatabanken
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.core import QgsPoint, QgsFeature, QgsGeometry, QgsVectorLayer, QgsField, QgsRectangle
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsPointXY
from PyQt5.QtCore import QVariant
from qgis.core import QgsProject



# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .Artdatabanken_plugin_dialog import ArtdatabankenDialog, FirstPopupDialog, ArtTypeDialog, WFSInfoDialog, \
    ArtAttDialog
from .load_data import from_wfs, to_map_art, to_map_area
import os.path
from .api_handler import APIClient


class Artdatabanken:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Artdatabanken_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Artdatabanken')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        # Initialize the APIClient with your API key and the base URL of the API
        self.api_key = "5044b6436a6b4814b9689cd6fac542f0"  # Replace with your actual API key
        self.base_url_area = "https://api.artdatabanken.se/species-observation-system/v1/Areas"  # Base URL of the API, area
        self.base_url_art = "https://api.artdatabanken.se/species-observation-system/v1/Observations/Search/DwC"  # Base URL of the API, art

        # Create an instance of APIClient
        self.api_client_area = APIClient(self.api_key, self.base_url_area)
        self.api_client_art = APIClient(self.api_key, self.base_url_art)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Artdatabanken', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Artdatabanken_plugin/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'link data'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Artdatabanken'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.Fpop = FirstPopupDialog()

        self.Fpop.show()
        # Run the dialog event loop

        self.Fpop.loadDataButton.clicked.connect(self.show_second_dialog)
        # See if OK was pressed

    def show_second_dialog(self):
        """Show the second dialog after the first one."""
        area_info_checked = self.Fpop.form_class.isChecked()
        art_info_checked = self.Fpop.art_info.isChecked()
        wfs_info_checked = self.Fpop.WFS_info.isChecked()

        if area_info_checked:
            self.dlg = ArtdatabankenDialog()
            self.populate_area_types()
            self.dlg.loadDataButton.clicked.connect(lambda: to_map_area(self))
            self.dlg.show()

        if art_info_checked:
            self.art = ArtTypeDialog()
            self.art_type()
            self.art.loadDataButton.clicked.connect(lambda: self.on_art_load())
            self.art.show()


        if wfs_info_checked:
            self.wfs = WFSInfoDialog()
            self.wfs.loadDataButton.clicked.connect(lambda: from_wfs(self))
            self.wfs.show()

        if not (area_info_checked or art_info_checked or wfs_info_checked):
            self.iface.messageBar().pushMessage(
                "Select a type of data", level=3)

        self.Fpop.close()

    def on_art_load(self):
        self.attA = ArtAttDialog()
        self.attA.loadDataButton.clicked.connect(lambda: to_map_art(self))
        self.attA.show()
    def populate_area_types(self):
        area_types_data = [
            "Municipality", "Community", "Sea", "CountryRegion", "NatureType",
            "Province", "Ramsar", "BirdValidationArea", "Parish", "Spa",
            "County", "ProtectedNature", "SwedishForestAgencyDistricts",
            "Sci", "WaterArea", "Atlas5x5", "Atlas10x10", "SfvDistricts", "Campus"
        ]

        self.dlg.areaType.clear()  # Clear any existing items
        self.dlg.areaType.addItems(area_types_data)  # Add area types to the dropdown

    def art_type(self):
        art_type_data = ["","Plantae", "Arachnida", "Mollusca", "Insecta", "Amphibia", "Aves",
                         "Mammalia", "Reptilia", "Actinopterygii", "Animalia", "Fungi"]
        self.art.artType.clear()
        self.art.artType.addItems(art_type_data)

