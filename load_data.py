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
            endpoint = base_url  # name is provided

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
        selected_art_types = [item.text() for item in self.art.artType.selectedItems()]
        print("Selected Art Types:", selected_art_types)

        selected_scientific_names = self.art.scientificName.text()
        print(f"Selected scientific names: {selected_scientific_names}")



        scientific_names = [name.strip() for name in selected_scientific_names.split(",") if name.strip()]



        selected_nbrPoints = self.art.maxNbr_art.text()


        if not selected_nbrPoints.isnumeric() or int(selected_nbrPoints) <= 0:
            self.iface.messageBar().pushMessage(
                "Error", "Please input a positive numerical value.", level=3
            )
            return

        nbr_points = int(selected_nbrPoints)

        # Fetch data from the API
        endpoint = ""

        # To handle requests with more than 1000 takes
        skips = 0
        nbr_points_left = nbr_points
        all_data = []

        # Construct the query parameters and run API depending on the number of takes
        while nbr_points_left > 0:
            params_art = {
                "kingdom": ",".join(selected_art_types),
                "scientificName": ",".join(scientific_names),
                "skip": skips,
                "take": min(1000, nbr_points_left),  # Take up to 1000 records
            }

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

            all_data.extend(data)  # Add the new data to the existing data list

            # Update remaining points and skip for the next API call
            nbr_points_left -= len(data)  # Adjust remaining points
            skips += len(data)  # Increase skip based on the amount of data received

        # Now we have all data in `all_data`, proceed to create the QGIS layer
        if not all_data:
            self.iface.messageBar().pushMessage(
                "Error", "No data returned from the API.", level=3
            )
            return

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

        for record in all_data:
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


import urllib.parse

def to_map_area(self):
    try:
        # Select area type from the drop-down menu
        selected_area_types = [
            item.text() for item in self.dlg.areaType_2.selectedItems()
        ]

        # Ensure selected_area_types is not empty
        if not selected_area_types:
            self.iface.messageBar().pushMessage(
                "Error", "Please select at least one area type.", level=3
            )
            return

        # Construct the areaTypes parameter with multiple keys (URL-encoded)
        area_type_params = "&".join(
            [f"areaTypes={urllib.parse.quote(area)}" for area in selected_area_types]
        )

        # Get selected attributes (if applicable)
        selected_attributes = [
            checkbox.text() for checkbox in self.dlg.checkboxes if checkbox.isChecked()
        ]
        print(f"Selected attributes: {selected_attributes}")


        # Limit for areaTypes (Max data points)
        area_type_point_limits = {
            "": (0, float('inf')),  # No limit for an empty area type
            "Municipality": (1, 290),
            "Community": (1, 1888),
            "Sea": (1, 8),
            "CountryRegion": (1, 4),
            "NatureType": (1, 6),
            "Province": (1, 34),
            "Ramsar": (1, 67),
            "BirdValidationArea": (1, 31),
            "Parish": (1, 2433),
            "Spa": (1, 550),
            "County": (1, 21),
            "ProtectedNature": (1, 6691),
            "SwedishForestAgencyDistricts": (1, 22),
            "Sci": (1, 3989),
            "WaterArea": (1, 925),
            "Atlas5x5": (1, 21921),
            "Atlas10x10": (1, 5636),
            "SfvDistricts": (1, 4),
            "Campus": (1, 5)
        }

        # Selected number of takes (points)
        selected_nbrPoints = self.dlg.maxNbr_area.text()

        if not selected_nbrPoints.isnumeric() or int(selected_nbrPoints) <= 0:
            self.iface.messageBar().pushMessage(
                "Error", "Please input a positive numerical value.", level=3
            )
            return
        nbr_points = int(selected_nbrPoints)

        # Check limits for each selected area type
        # Calculate the total maximum points across selected area types
        total_min_points = 0
        total_max_points = 0

        for area_type in selected_area_types:
            min_points, max_points = area_type_point_limits.get(area_type, (1, 100))
            total_min_points += min_points
            total_max_points += max_points

        # Check if the user's input exceeds the combined limit
        if  nbr_points > total_max_points:
            self.dlg.maxLimitReachedLabel.setText(
                f"Limit exceeded! Total allowed points: {total_max_points}."
                f" "
                f"You requested: {nbr_points}."
            )
            self.dlg.maxLimitReachedLabel.setVisible(True)
            return  # Stop further execution
        else:
            self.dlg.maxLimitReachedLabel.setVisible(False)

        # Define query parameters
        params_area = {
            "searchString": "",
            "skip": 0,
            "take": nbr_points,
        }

        # Construct the full endpoint URL with the areaTypes parameter
        endpoint = "Areas"
        query_string = f"{urllib.parse.urlencode(params_area)}&{area_type_params}"
        full_url = f"{endpoint}?{query_string}"

        print(f"Sending API Request to: {full_url}")

        # Fetch data from the API
        data = self.api_client_area.fetch_data(endpoint=full_url)

        # Process the data (implement according to your application logic)
        print(f"Received data: {data}")


        # Validate the response
        if not data or "records" not in data:
            print(f"API Response Error: {data}")
            self.iface.messageBar().pushMessage(
                "Error", "Invalid or empty response from the API.", level=3
            )
            return

        records = data.get("records", [])
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

