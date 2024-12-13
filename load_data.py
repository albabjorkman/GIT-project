from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.core import QgsPoint, QgsFeature, QgsGeometry, QgsVectorLayer, QgsField, QgsRectangle
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsPointXY
from PyQt5.QtCore import QVariant
from qgis.core import QgsProject
import requests


def from_wfs(self):
    """Fetch data from the WFS service and load it as points on the map."""
    try:
        # Define the WFS URL
        url = "https://sosgeo.artdata.slu.se/geoserver/SOS/ows?service=wfs&version=2.0.0&request=GetFeature&typeName=SOS:SpeciesObservations&outputFormat=application/json&count=100"

        # Send a GET request to fetch the data
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()  # Parse the JSON response

            # Log the full response to inspect the data
            print("Response data:", data)

            # Create a new vector layer for points
            layer = QgsVectorLayer("Point?crs=EPSG:4326", "WFS Data Points", "memory")
            provider = layer.dataProvider()

            # Define the fields (attributes) for the layer
            provider.addAttributes([
                QgsField("vernacularName", QVariant.String),
                QgsField("ObservationID", QVariant.String),
                QgsField("Location", QVariant.String),
            ])
            layer.updateFields()

            # Set to track unique points with some precision tolerance
            processed_points = set()
            print(data)

            # Function to round coordinates for comparison
            def round_coordinates(lon, lat, precision=5):
                return (round(lon, precision), round(lat, precision))

            # Process each record and add a point feature
            for feature in data.get("features", []):
                geometry = feature.get("geometry")
                if geometry:
                    coords = geometry.get("coordinates", [])
                    if len(coords) >= 2:  # Assuming coordinates are [longitude, latitude]
                        lon, lat = coords[0], coords[1]

                        # Round the coordinates for comparison
                        point_key = round_coordinates(lon, lat)

                        # Skip if the point has already been processed
                        if point_key in processed_points:
                            continue

                        # Mark this point as processed
                        processed_points.add(point_key)

                        # Create a feature for the point
                        point = QgsPointXY(lon, lat)
                        qgis_feature = QgsFeature()
                        qgis_feature.setGeometry(QgsGeometry.fromPointXY(point))

                        # Set attributes (example: species and observation ID)
                        qgis_feature.setAttributes([
                            feature.get("vernacularName", ""),
                            feature.get("vernacularName", {}).get("vernacularName", "Unknown"),
                            f"Lat: {lat}, Lon: {lon}",
                        ])

                        # Add feature to the provider
                        provider.addFeature(qgis_feature)

            # Update layer extents and add to QGIS project
            layer.updateExtents()
            QgsProject.instance().addMapLayer(layer)

            self.iface.messageBar().pushMessage("Success", "WFS data loaded successfully as points.", level=1)
        else:
            self.iface.messageBar().pushMessage("Error", "Failed to retrieve data from WFS.", level=3)
            print(f"Failed to retrieve data. Status code: {response.status_code}")
    except Exception as e:
        self.iface.messageBar().pushMessage(
            "Error", f"Failed to load data: {str(e)}", level=3
        )
        print(f"Error: {str(e)}")


def to_map_art(self):
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
            "take": 10,  # Limit to a maximum of 100 records
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
            QgsField("eventID", QVariant.String),
            QgsField("identificationID", QVariant.String),
            QgsField("continent", QVariant.String),
            QgsField("kingdom", QVariant.String),
            QgsField("scientificName", QVariant.String),
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
                        str(record.get("eventID", "")),
                        record.get("identificationID", ""),
                        record.get("continent", ""),
                        record.get("kingdom", ""),
                        record.get("scientificName", ""),
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

def to_map_area(self):
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
            "take": 10,
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
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "Area Data Points", "memory")
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