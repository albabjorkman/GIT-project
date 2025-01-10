# Artdatabanken QGIS Plugin ReadMe
Unofficial plugin for extracting data from the Swedish Artdatabankens database.\
Created by three students in conjunction with the EXTP40 - GIT-project course at Lund University in 2025.

# Plugin Structure
The plugin consists of three different request which utilizes either APIs available at Artdatabanken, getAreas and ObservationsSearchByDwc, or the Species Observation System (SOS) WFS Service. <br>
<img src="Git_pictures/first_pop_up.png" alt="First dialog window" width="400"/>
<br>
Links on dialog window are:
<br>
[API information](https://api-portal.artdatabanken.se/api-details#api=sos-api-v1)
<br>
[WFS information GITHUB](https://github.com/biodiversitydata-se/SOS/blob/master/Docs/WfsService.md)

## Overall information about input
The plugin allows for case-insensitive input, meaning capital letters don’t matter, and it supports letters like Å, Ä, and Ö. To search for multiple items, use a comma (,) between each species. Spelling is critical for accurate results, so ensure inputs are correct. The calendar works from 1752 onward, though Artdatabanken offers older data. By default, criteria are combined with an “AND” unless stated otherwise.

## Areas request

## Species Observations request

## WFS request
