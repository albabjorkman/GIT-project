from qgis.core import QgsPoint, QgsFeature, QgsGeometry, QgsVectorLayer, QgsField, QgsRectangle
from qgis.core import QgsProject, QgsVectorLayer, QgsPointXY, QgsWkbTypes, QgsCoordinateReferenceSystem, \
    QgsCoordinateTransform
from PyQt5.QtCore import QVariant
import requests
from datetime import datetime
import urllib.parse
from shapely.wkt import loads, dumps
from shapely.geometry import MultiPolygon, Polygon


def from_wfs(self):
    # fetch data from the WFS service and load it as points on the map with selectable attributes
    try:
        # Define the WFS URL with added CQL filter
        base_url = "https://sosgeo.artdata.slu.se/geoserver/SOS/ows?service=wfs&version=2.0.0&request=GetFeature&typeName=SOS:SpeciesObservations&outputFormat=application/json&CQL_Filter="

        # load in the added option from first pop-up window from WFS
        selected_scientific_names = self.wfsS.scientificName.text()
        selected_area_names = self.wfsS.writeAreaType.text()
        selected_vernacular_names = self.wfsS.vernacularName.text()
        start_date = self.wfsS.startDate.date().toString("yyyy-MM-dd")
        end_date = self.wfsS.endDate.date().toString("yyyy-MM-dd")

        # Validate input dates (shouldn't be an issue due to calendar input but still)
        if start_date and end_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                self.iface.messageBar().pushMessage(
                    "Error", "Invalid date format."
                )

        # Loading in the radiobuttom if want OR or AND in between scientific name and vernacular name
        combine_with = "AND"  # Default logical operator
        if self.wfsS.AND.isChecked():
            combine_with = "AND"
        elif self.wfsS.OR.isChecked():
            combine_with = "OR"

        # Lists that hold different filters used to construct endpoint call
        filters_name = []
        filter_date = []
        filter_geom = []
        filter_area = []

        # Construct the endpoint based on scientific name input
        if selected_scientific_names:
            names = [name.strip() for name in selected_scientific_names.split(",") if name.strip()]
            if not names:
                self.iface.messageBar().pushMessage(
                    "Error", "Please provide valid scientific names.", level=3
                )
                return

            name_filter = "(" + " OR ".join([f"scientificName='{name}'" for name in names]) + ")"
            filters_name.append(name_filter)

        # Construct the endpoint based on vernacular name input
        if selected_vernacular_names:
            names = [name.strip() for name in selected_vernacular_names.split(",") if name.strip()]
            if not names:
                self.iface.messageBar().pushMessage(
                    "Error", "Please provide valid vernacular names.", level=3
                )
                return

            name_filter = "(" + " OR ".join([f"vernacularName='{name}'" for name in names]) + ")"
            filters_name.append(name_filter)

        # Construct the endpoint based on logical operation, vernacular, scientific name
        cql_name_filter = f"({combine_with.join(filters_name)})" if filters_name else ""

        if selected_area_names:

            area = self.wfsS.AreaType.currentText()
            if not area or area == "":  # Check if no area is selected
                self.iface.messageBar().pushMessage(
                    "Error", "Please select an Area Type before providing area names.", level=3
                )
                return
            names = [name.strip() for name in selected_area_names.split(",") if name.strip()]
            if not names:
                self.iface.messageBar().pushMessage(
                    "Error", "Please provide valid scientific names.", level=3
                )
                return

            name_filter = "(" + " OR ".join([f"{area}='{name}'" for name in names]) + ")"
            filter_area.append(name_filter)

        # Add start- and end-date to filters
        if start_date and end_date:
            start_date_filter = f"startDate>='{start_date}'"
            end_date_filter = f"endDate<='{end_date}'"
            filter_date.append(f"{start_date_filter} AND {end_date_filter}")

        # Polygon filter to add to URL in correct way
        filter_geom = None
        selected_layer = self.wfsS.polygonLayerComboBox.currentText()

        if selected_layer != "No polygon": #skip step if no added polygon
            try:
                polygon_layer = QgsProject.instance().mapLayersByName(selected_layer)[0]
                if polygon_layer:
                    polygon_filters = []
                    for feature in polygon_layer.getFeatures():
                        geometry = feature.geometry()
                        if geometry:
                            # Transform geometry to WGS84
                            crs_transform = QgsCoordinateTransform(
                                polygon_layer.crs(),
                                QgsCoordinateReferenceSystem("EPSG:4326"),
                                QgsProject.instance()
                            )
                            geometry.transform(crs_transform)

                            # Convert geometry to WKT
                            polygon_wkt = geometry.asWkt()
                            
                            # Use swap_coordinates function to change order of long and lat
                            # loads() and dumps() are shapely function that in this case transform objects between geom and wkt objects
                            poly_geom = loads(polygon_wkt)
                            swapped_geom = swap_coordinates(poly_geom)
                            swapped_wkt = dumps(swapped_geom)

                            # pointLocation geometry type required due to observations being output as points
                            polygon_filters.append(f"INTERSECTS(pointLocation,{swapped_wkt})")
                            
                        if polygon_filters:
                            # This generates the CQL filter that can be appended to the URL
                            filter_geom = f"({' OR '.join(polygon_filters)})"
                            print(f"Polygon Filter: {filter_geom}")

            except IndexError:
                self.iface.messageBar().pushMessage("Error", "Selected polygon layer not found.", level=3)
            except Exception as e:
                self.iface.messageBar().pushMessage("Error", f"Error processing polygon layer: {str(e)}", level=3)

        # Join all filters together to contruct final endpoint
        all_filters = []
        if cql_name_filter:
            all_filters.append(cql_name_filter)
        if filter_date:
            all_filters.append(" AND ".join(filter_date))
        if filter_geom:
            all_filters.append(filter_geom)
        if filter_area:
            all_filters.append(" OR ".join(filter_area))

        # final endpoint and print control to see it correct
        cql_filter = urllib.parse.quote(" AND ".join(all_filters)) if all_filters else ""
        print(cql_filter)

        # Create a new vector layer for points
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "WFS Data Points", "memory")
        provider = layer.dataProvider()

        # Get selected attributes from checkboxes (the text of each checkbox)
        selected_attributes = [
            checkbox.text()  # This will fetch the name set in QCheckBox
            for checkbox in self.wfs.checkboxes
            if checkbox.isChecked()
        ]
        print(f"Selected attributes: {selected_attributes}")

        # error if not show anything in attribute table
        if not selected_attributes:
            self.iface.messageBar().pushMessage(
                "Error", "Please select at least one attribute.", level=3
            )
            return

        # Create the fields based on selected attributes
        fields = [QgsField(attr, QVariant.String) for attr in selected_attributes]
        provider.addAttributes(fields)
        layer.updateFields()

        # Input and check max points
        selected_nbrPoints = self.wfsS.maxNbr_WFS.text()
        if not selected_nbrPoints.isnumeric() or int(selected_nbrPoints) <= 0:
            self.iface.messageBar().pushMessage(
                "Error", "Please input a positive numerical value.", level=3
            )
            return

        # Convert to int and define max features per request and max start index
        max_points = int(selected_nbrPoints)
        max_features_per_request = 5000
        max_start_index = 100000

        # Fetch data in batches
        start_index = 0
        total_features = []

        # to do until selected nbr of points, WFS have maximum of point, to go over this max. Max number to stuck in loop
        while start_index < max_start_index and len(total_features) < max_points:
            remaining_points = max_points - len(total_features)
            request_count = min(remaining_points, max_features_per_request)
            endpoint = f"{base_url}{cql_filter}&startIndex={start_index}&count={request_count}"
            print(endpoint)

            response = requests.get(endpoint)

            # if not can fetch data
            if response.status_code != 200:
                self.iface.messageBar().pushMessage(
                    "Error", f"Failed to retrieve data: HTTP {response.status_code}", level=3
                )
                return

            data = response.json()
            features = data.get("features", [])

            if not features:
                return

            total_features.extend(features)
            start_index += request_count

            if len(features) < request_count:
                break

        # Set to track unique points with some precision tolerance
        processed_points = set()

        # adding the features as points on map
        for feature in total_features:
            geometry = feature.get("geometry")
            if geometry:
                coords = geometry.get("coordinates", [])
                if len(coords) >= 2:  # Assuming coordinates are [longitude, latitude]
                    lon, lat = coords[0], coords[1]

                    point_key = lon, lat

                    # Skip if doublets points (if that option is checked)
                    if not self.wfsS.double.isChecked():
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

    # Exception block
    except Exception as e:
        self.iface.messageBar().pushMessage(
            "Error", f"Failed to load data: {str(e)}", level=3
        )

# function to convert WKT coordinates from long/lat to lat/long
def swap_coordinates(geometry):
    if geometry.geom_type == 'Polygon':
        # Handle Polygon object
        new_shell = [(y, x) for x, y in geometry.exterior.coords]
        new_holes = [
            [(y, x) for x, y in ring.coords]
            for ring in geometry.interiors
        ]
        return Polygon(new_shell, new_holes)

    elif geometry.geom_type == 'MultiPolygon':
        # Handle MultiPolygon object
        new_polygons = []
        for polygon in geometry.geoms:
            new_shell = [(y, x) for x, y in polygon.exterior.coords]
            new_holes = [
                [(y, x) for x, y in ring.coords]
                for ring in polygon.interiors
            ]
            new_polygons.append(Polygon(new_shell, new_holes))
        return MultiPolygon(new_polygons)
    else:
        raise ValueError("Only polygons and Multipolygons supported")


# loading data for species API
def to_map_art(self):
    try:
        # Select species type (kingdom) from the drop-down menu + control of valid
        selected_art_types = [item.text() for item in self.art.artType.selectedItems()]
        print("Selected Art Types:", selected_art_types)

        # Select scientific name written + control of valid
        selected_scientific_names = self.art.scientificName.text()
        print(f"Selected scientific names: {selected_scientific_names}")

        # if several added these are change for the API to work correctly
        scientific_names = [name.strip() for name in selected_scientific_names.split(",") if name.strip()]

        # read nbr of point wanting + error if this is not working as INT
        selected_nbrPoints = self.art.maxNbr_art.text()

        if not selected_nbrPoints.isnumeric() or int(selected_nbrPoints) <= 0:
            self.iface.messageBar().pushMessage(
                "Error", "Please input a positive numerical value.", level=3
            )
            return

        # change string to INT
        nbr_points = int(selected_nbrPoints)

        # Date interval for events, chosen by input
        startEventDate = self.art.startDate.date().toString("yyyy-MM-dd")
        endEventDate = self.art.endDate.date().toString("yyyy-MM-dd")

        # Validate input dates (shouldn't be an issue due to calendar input but still)
        if startEventDate and endEventDate:
            try:
                datetime.strptime(startEventDate, "%Y-%m-%d")
                datetime.strptime(endEventDate, "%Y-%m-%d")
            except ValueError:
                self.iface.messageBar().pushMessage(
                    "Error", "Invalid date format."
                )

        # basic endpoint if nothing more added
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
                "minEventDate": startEventDate,
                "maxEventDate": endEventDate,
                "skip": skips,
                "take": min(1000, nbr_points_left),  # Take up to 1000 records
            }

            # fetching data  with params and endpoint in API handler
            try:
                data = self.api_client_art.fetch_data(endpoint=endpoint, params=params_art)
            except Exception as fetch_error:
                self.iface.messageBar().pushMessage(
                    "Error", f"Failed to fetch data: {str(fetch_error)}", level=3
                )
                return

            if not data or not isinstance(data, list):
                self.iface.messageBar().pushMessage(
                    "Error", "Invalid or empty response from the API.", level=3
                )
                return

            all_data.extend(data)  # Add the new data to the existing data list

            # Update remaining points and skip for the next API call
            nbr_points_left -= len(data)
            skips += len(data)  # Increase skip based on the amount of data received

        # Check All data in `all_data`
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

        # error so no empty attribute table
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

        # Define `processed_points` outside the loop
        processed_points = set()

        for record in all_data:

            try:
                # Extract latitude and longitude
                lat = record.get("decimalLatitude")
                lon = record.get("decimalLongitude")

                # Skip processing if coordinates are missing
                if lat is None or lon is None:
                    print(f"Skipping record due to missing coordinates: {record}")
                    continue  # Skip this record

                # Check for duplicates
                point_key = (lat, lon)  # Create a tuple to represent the point uniquely
                if not self.art.double.isChecked():  # If "no duplicates" is selected to not get duplicates
                    if point_key in processed_points:
                        print(f"Skipping duplicate point: {point_key}")
                        continue  # Skip point
                    processed_points.add(point_key)  # Mark point as processed

                print(f"Adding feature with coordinates: {lon}, {lat}")  # Debugging

                # Create feature geometry (point)
                point = QgsPointXY(lon, lat)
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPointXY(point))

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


# function to load data from Area API
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
        if nbr_points > total_max_points:
            self.dlg.maxLimitReachedLabel.setText(
                f"Limit exceeded!\nTotal allowed points: {total_max_points}"
            )
            self.dlg.maxLimitReachedLabel.setVisible(True)

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
                attributes = [
                    record.get(attr, "") for attr in selected_attributes
                ]

                feature.setAttributes(attributes)
                provider.addFeature(feature)
                layer.updateFields()

        layer.updateExtents()
        QgsProject.instance().addMapLayer(layer)
        self.iface.messageBar().pushMessage("Success", "Data loaded successfully as points.", level=1)

    except Exception as e:
        self.iface.messageBar().pushMessage(
            "Error", f"Failed to load data: {str(e)}", level=3
        )
        print("Error:", str(e))
