from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.core import QgsPoint, QgsFeature, QgsGeometry, QgsVectorLayer, QgsField, QgsRectangle
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsPointXY
from PyQt5.QtCore import QVariant
from qgis.core import QgsProject
import requests


def from_wfs(self):
    """Fetch data from the WFS service and load it as points on the map with selectable attributes."""
    try:
        # Define the WFS URL
        base_url = "https://sosgeo.artdata.slu.se/geoserver/SOS/ows?service=wfs&version=2.0.0&request=GetFeature&typeName=SOS:SpeciesObservations&outputFormat=application/json&count=5&CQL_Filter="

        selected_scientific_names = self.wfsS.scientificName.text()
        print(f"Selected scientific name: {selected_scientific_names}")

        # Construct the endpoint dynamically based on scientific name input
        if selected_scientific_names:
            names = [name.strip() for name in selected_scientific_names.split(",") if name.strip()]
            if not names:
                self.iface.messageBar().pushMessage(
                    "Error", "Please provide valid scientific names.", level=3
                )
                return

            # Create CQL filter for multiple names
            filters = " OR ".join([f"scientificName='{name}'" for name in names])
            endpoint = f"{base_url}{filters}"
        else:
            endpoint = base_url  #  name is provided



        # Send a GET request to fetch the data
        response = requests.get(endpoint)

        if response.status_code == 200:
            data = response.json()  # Parse the JSON response

            # Log the full response to inspect the data
            print("Response data:", data)

            # Create a new vector layer for points
            layer = QgsVectorLayer("Point?crs=EPSG:4326", "WFS Data Points", "memory")
            provider = layer.dataProvider()

            # Get selected attributes from checkboxes (the text of each checkbox)
            selected_attributes = [
                checkbox.text()  # This will fetch the name set in the <string> property of QCheckBox
                for checkbox in self.wfs.checkboxes
                if checkbox.isChecked()
            ]
            print(f"Selected attributes: {selected_attributes}")

            if not selected_attributes:
                self.iface.messageBar().pushMessage(
                    "Error", "Please select at least one attribute.", level=3
                )
                return

            # Dynamically create the fields based on selected attributes
            fields = [QgsField(attr, QVariant.String) for attr in selected_attributes]
            provider.addAttributes(fields)
            layer.updateFields()

            # Set to track unique points with some precision tolerance
            processed_points = set()

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

                        # Create feature geometry (point)
                        point = QgsPointXY(lon, lat)
                        qgis_feature = QgsFeature()
                        qgis_feature.setGeometry(QgsGeometry.fromPointXY(point))

                        # Collect attributes based on selected fields
                        attributes = [
                            feature.get("properties", {}).get(attr, "Unknown") for attr in selected_attributes
                        ]
                        qgis_feature.setAttributes(attributes)

                        # Add feature to the provider
                        provider.addFeature(qgis_feature)

            # Finalize the layer and add it to the QGIS project
            layer.updateExtents()
            QgsProject.instance().addMapLayer(layer)

            # Notify the user of success
            self.iface.messageBar().pushMessage(
                "Success", "WFS data loaded successfully as points.", level=1
            )
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

        selected_scientific_names = self.art.scientificName.text()
        print(f"Selected scientific names: {selected_scientific_names}")

        names = [name.strip() for name in selected_scientific_names.split(",") if name.strip()]
        if not names:
            self.iface.messageBar().pushMessage(
                "Error", "Please provide at least one valid scientific name.", level=3
            )
            return

        # Construct the query parameters
        params_art = {
            "kingdom": selected_art_type,  # Ensure `selected_art_type` matches allowed values
            "scientificName": ",".join(names),  # API accepts comma-separated names
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
            return

        if not data or not isinstance(data, list):
            self.iface.messageBar().pushMessage(
                "Error", "Invalid or empty response from the API.", level=3
            )
            return

        print(f"Fetched {len(data)} records from the API.")
        print(f"Fetched data: {data}")

        # Create a new vector layer for points
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "Species Observations", "memory")
        provider = layer.dataProvider()
        print(f"Layer valid: {layer.isValid()}")

        # Get selected attributes from checkboxes (the text of each checkbox)
        selected_attributes = [
            checkbox.text()  # This will fetch the name set in the <string> property of QCheckBox
            for checkbox in self.attA.checkboxes
            if checkbox.isChecked()
        ]
        print(selected_attributes)

        if not selected_attributes:
            self.iface.messageBar().pushMessage(
                "Error", "Please select at least one attribute.", level=3
            )
            return

        print(f"Selected attributes: {selected_attributes}")

        # Update the fields dynamically based on selected attributes
        fields = [QgsField(attr, QVariant.String) for attr in selected_attributes]
        provider.addAttributes(fields)
        layer.updateFields()


        for record in data:
            print(f"Processing record: {record}")  # Log to inspect the data

            try:
                # Extract latitude and longitude
                lat = record.get("decimalLatitude")
                lon = record.get("decimalLongitude")

                # Check if lat and lon are valid
                if lat is None or lon is None:
                    print(f"Skipping record due to missing coordinates: {record}")
                    continue  # Skip this record if coordinates are missing

                print(f"Adding feature with coordinates: {lon}, {lat}")  # Debugging print statement

                # Create feature geometry (point)
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))

                # Collect attributes based on selected fields
                attributes = [
                    record.get(attr, "Unknown") for attr in selected_attributes
                ]
                feature.setAttributes(attributes)

                # Add the feature to the provider
                provider.addFeature(feature)

            except Exception as feature_error:
                print(f"Error processing record: {record}, Error: {feature_error}")

        # Finalize the layer and add it to the QGIS project
        layer.updateExtents()
        QgsProject.instance().addMapLayer(layer)


        # Notify the user of success
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
        selected_area_type = self.dlg.areaType_2.currentText().strip()

        selected_attributes = [
            checkbox.text()
            for checkbox in self.dlg.checkboxes
            if checkbox.isChecked()
        ]
        print(f"Selected attributes: {selected_attributes}")

        # Define query parameters
        params_area = {
            "searchString": "",
            "skip": 0,
            "take": 10,
        }

        # Add areaTypes only if it's not empty
        if selected_area_type:
            params_area["areaType_2"] = selected_area_type

        print(f"Sending API Request with parameters: {params_area}")

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

        # Create fields
        fields = [QgsField(attr, QVariant.String) for attr in selected_attributes]
        provider.addAttributes(fields)
        layer.updateFields()

        # Process records
        for record in records:
            if "boundingBox" in record and "featureId" in record:
                bbox = record["boundingBox"]
                min_lon = bbox["bottomRight"]["longitude"]
                min_lat = bbox["bottomRight"]["latitude"]
                max_lon = bbox["topLeft"]["longitude"]
                max_lat = bbox["topLeft"]["latitude"]

                center_lon = (min_lon + max_lon) / 2
                center_lat = (min_lat + max_lat) / 2

                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(center_lon, center_lat)))
                feature.setAttributes([record.get(attr, "") for attr in selected_attributes])
                provider.addFeature(feature)

        layer.updateExtents()
        QgsProject.instance().addMapLayer(layer)
        self.iface.messageBar().pushMessage("Success", "Data loaded successfully as points.", level=1)

    except Exception as e:
        self.iface.messageBar().pushMessage(
            "Error", f"Failed to load data: {str(e)}", level=3
        )
        print("Error:", str(e))

