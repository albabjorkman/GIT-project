# Artdatabanken QGIS Plugin ReadMe
Unofficial plugin for extracting data from the Swedish Artdatabankens database.\
Created by Matilda Bengtsson, Alba Björkman and Albin Röcklinger, in the course EXTP40 - GIT Project with Python Programming, at Lund University in 2025.

# Plugin Structure
The plugin consists of three different request which utilizes either APIs available at Artdatabanken, getAreas and ObservationsSearchByDwc, or the Species Observation System (SOS) WFS Service. <br>
## Initial window
The window includes a selection that can be made between three different types of output: regions, species observations and WFS.
<img src="Git_pictures/first_pop_up.png" alt="First dialog window" width="400"/>
<br>
Links on dialog window are:
<br>
[API information](https://api-portal.artdatabanken.se/api-details#api=sos-api-v1)
<br>
[WFS information GITHUB](https://github.com/biodiversitydata-se/SOS/blob/master/Docs/WfsService.md)

### Overall information about input
The plugin allows for case-insensitive input, meaning capital letters don’t matter, and it supports letters like Å, Ä, and Ö. To search for multiple items, use a comma (,) between each species. Spelling is critical for accurate results, so ensure inputs are correct. The calendar works from 1752 onward, though Artdatabanken offers older data. By default, criteria are combined with an “AND” unless stated otherwise.

## Areas request
Output is in the form of points which show the locations of different area classifications in Sweden. <br>
<img src="Git_pictures/Areas.png" alt="Area request" width="400"/>

Item 1: Selection window, the different area types created by Artdatabanken can be found here. More than one option can be chosen and for all area types, choose the empty box on the first row. <br>
Item 2: Input box for the amount of observations the user wants output. <br>
Item 3: Checkboxes for specifying which attributes the user wants the point objects to contain. <br>
Item 4: Select/Clear all buttons, selects or clears all attributes in item 3. <br>

## Species Observations request

## WFS request
