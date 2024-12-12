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
import urllib.request

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .Artdatabanken_plugin_dialog import ArtdatabankenDialog, FirstPopupDialog, ArtTypeDialog
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

        if art_info_checked and area_info_checked:
            self.Fpop.close()
            self.dlg = ArtdatabankenDialog()
            self.populate_area_types()
            self.dlg.loadDataButton.clicked.connect(self.load_data_to_map_art)
            self.dlg.show()

            self.art = ArtTypeDialog()
            self.art_type()
            self.art.loadDataButton.clicked.connect(self.load_data_to_map_art)  # Ensure connection
            self.art.show()
        elif area_info_checked:
            # Close the first popup
            self.Fpop.close()
            # Initialize the second dialog if not already done
            self.dlg = ArtdatabankenDialog()
            # Populate the area types dropdown in the second dialog
            self.populate_area_types()
            # Connect the "Load Data" button to its functionality
            self.dlg.loadDataButton.clicked.connect(self.load_data_to_map_area)
            # Show the second dialog
            self.dlg.show()
        elif art_info_checked:
            self.Fpop.close()
            self.art = ArtTypeDialog()
            self.art_type()
            self.art.loadDataButton.clicked.connect(self.load_data_to_map_art)
            self.art.show()
        else:
            self.iface.messageBar().pushMessage(
                "Select a type of data", level=3)

    def load_data_to_map_area(self):
        try:
            # Select area type from the drop-down menu
            selected_area_type = self.dlg.areaType.currentText()
            if not selected_area_type:
                self.iface.messageBar().pushMessage(
                    "Error", "Please select an area type.", level=3
                )
                return

            # Define query parameters
            params_area = {
                "areaTypes": selected_area_type,
                "searchString": "",
                "skip": 0,
                "take": 100,
            }

            # Fetch data from the API
            endpoint = ""
            data = self.api_client_area.fetch_data(endpoint=endpoint, params=params_area)

            if not data or "records" not in data:
                self.iface.messageBar().pushMessage(
                    "Error", "Invalid or empty response from the API.", level=3
                )
                return

            records = data["records"]
            print(f"Fetched {len(records)} records from the API.")

            # Create a new vector layer for points
            layer = QgsVectorLayer("Point?crs=EPSG:4326", "API Data Points", "memory")
            provider = layer.dataProvider()

            # Define the fields (attributes) for the layer
            provider.addAttributes([
                QgsField("Name", QVariant.String),
                QgsField("FeatureID", QVariant.String),
                QgsField("AreaType", QVariant.String),
            ])
            layer.updateFields()

            # Process each record and add a point feature
            for record in records:
                if "boundingBox" in record and "featureId" in record:
                    bbox = record["boundingBox"]
                    min_lon = bbox["bottomRight"]["longitude"]
                    min_lat = bbox["bottomRight"]["latitude"]
                    max_lon = bbox["topLeft"]["longitude"]
                    max_lat = bbox["topLeft"]["latitude"]

                    # Calculate center of the bounding box
                    center_lon = (min_lon + max_lon) / 2
                    center_lat = (min_lat + max_lat) / 2

                    # Create a feature for the center point
                    feature = QgsFeature()
                    feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(center_lon, center_lat)))

                    # Set attributes for the feature
                    feature.setAttributes([
                        record.get("name", "Unknown"),
                        record.get("featureId", "Unknown"),
                        record.get("areaType", "Unknown"),
                    ])

                    # Add feature to the provider
                    provider.addFeature(feature)

            # Update layer extents and add to QGIS project
            layer.updateExtents()
            QgsProject.instance().addMapLayer(layer)

            self.iface.messageBar().pushMessage("Success", "Data loaded successfully as points.", level=1)

        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error", f"Failed to load data: {str(e)}", level=3
            )
            print("Error:", str(e))

    def load_data_to_map_art(self):
        try:
            # Select art type from the drop-down menu
            selected_art_type = self.art.artType.currentText()
            print(f"Selected art type: {selected_art_type}")

            if not selected_art_type:
                self.iface.messageBar().pushMessage(
                    "Error", "Please select an art type.", level=3
                )
                return

            # Define query parameters
            params_art = {
                "kingdom": selected_art_type,  # Ensure `selected_art_type` matches allowed values
                "skip": 0,
                "take": 100,  # Limit to a maximum of 100 records
            }

            # Fetch data from the API
            endpoint = ""


            try:
                data = self.api_client_art.fetch_data(endpoint=endpoint, params=params_art)


            except Exception as fetch_error:
                self.iface.messageBar().pushMessage(
                    "Error", f"Failed to fetch data: {str(fetch_error)}", level=3
                )
                print(f"Error: Failed to fetch data: {str(fetch_error)}")
                print(f"API Response: {data}")
                return

            if not data or not isinstance(data, list):
                self.iface.messageBar().pushMessage(
                    "Error", "Invalid or empty response from the API.", level=3
                )
                return

            print(f"Fetched {len(data)} records from the API.")

            # Create a new vector layer for points
            layer = QgsVectorLayer("Point?crs=EPSG:4326", "Species Observations", "memory")
            provider = layer.dataProvider()

            # Define the fields (attributes) for the layer
            provider.addAttributes([
                QgsField("organismName", QVariant.String),
                QgsField("identificationID", QVariant.String),
                QgsField("kingdom", QVariant.String),
            ])
            layer.updateFields()

            # Process each record and add a point feature
            for record in data:
                try:
                    lat = record.get("decimalLatitude")
                    lon = record.get("decimalLongitude")

                    if lat is not None and lon is not None:
                        feature = QgsFeature()
                        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
                        feature.setAttributes([
                            record.get("eventID", ""),
                            record.get("location", ""),
                            record.get("kingdom", ""),
                        ])
                        provider.addFeature(feature)
                except Exception as feature_error:
                    print(f"Error processing record: {record}, Error: {feature_error}")

            # Update layer extents and add to QGIS project
            layer.updateExtents()
            QgsProject.instance().addMapLayer(layer)

            self.iface.messageBar().pushMessage(
                "Success", "Data loaded successfully as points.", level=1
            )

        except Exception as e:
            self.iface.messageBar().pushMessage(
                "Error", f"Failed to load data: {str(e)}", level=3
            )
            print(f"Error: {str(e)}")

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
        art_type_data = ["Plantae", "Arachnida", "Mollusca", "Insecta", "Amphibia", "Aves",
                         "Mammalia", "Reptilia", "Actinopterygii", "Animalia", "Fungi"]
        self.art.artType.clear()
        self.art.artType.addItems(art_type_data)
