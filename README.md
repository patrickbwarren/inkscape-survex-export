## Export an inkscape line drawing to a survex file

* _v2.1 minor improvements_
* _v2.0 completely rewritten for Inkscape 1.0_
* _v1.1 for Inkscape 0.92_

Use-cases include:

* producing a plausible length estimate for a drawn-up survey;
* georeferencing a drawn-up survey (see below);
* generating a skeleton to hang data off in a resurvey project;
* giving 'armchair cavers' something useful to do.

Some example surveys (Inkscape traced drawings) are also included.

This documentation is also available in [PDF](README.pdf) and
[HTML](README.html).

### Installation

Copy the files `svx_export.py` and `svx_export.inx` into your local
Inkscape extension folder, eg `$HOME/.config/inkscape/extensions/` on
unix, or `%APPDATA%\inkscape\extensions\` on Windows.

### Usage

The extension appears under Extensions &rarr; Export  &rarr;
Export drawing to .svx file&hellip;

The following conventions are observed:

* all (poly)lines of a given color (default _red_) are converted to traverses in the survex file;
* a line of a second color (default _blue_) sets the scale (eg from the scale bar);
* a line of a third color (default _green_) determines the orientation (default S to N).

Lines of any other color are ignored, as are other drawing objects.
The default _colors_ can be changed in the color tabs in the dialog box.

Exported (poly)lines are converted to traverses.  If there is more
than one traverse, each one is captured in a separate `*begin` and
`*end` block in the survex file using Inkscape path name so that
individual traverses can be matched up to the drawn paths. The
survey as a whole is wrapped in a top level `*begin` and `*end` block
with a name corresponding to the `.svx` file name following standard
conventions.

Within each traverse, survey legs are generated in the format

`*data normal from to tape compass clino`

where:

* The `from` and `to` stations are integers generated automatically.

* The `tape` length is generated using the scale line as reference,
which will usually be traced over a scale bar in the survey.  The true
length that the scale line represents is specified in the Parameters
tab in the export dialogue box.

* The `compass` bearing is generated using the orientation line as
reference, which for example will be traced over a North arrow in the
survey (in the direction S to N; corresponding to bearing = 0.0 in the
dialog box).  If a North arrow is not used the true bearing
represented by the orientation line should of course be specified in
the Parameters tab in the export dialogue box.

* The `clino` reading is set to zero.

Survey stations that are closer than a given specification are assumed
to be the same and given as an `*equate` at the start of the `.svx`
file.  The tolerance to select these (eg 0.2m) can be adjusted in the
Parameters tab in the export dialogue box.  Stations which feature in
this `*equate` are automatically exported out of the underlying
`*begin` and `*end` block by the appropriate `*export` commands.

### Workflow

Usually the drawing will be made by tracing over a scannned image of a
drawn-up survey.  A typical workflow might be as follows:

* start a new Inkscape document;
* import (link or embed) a scanned survey as an image;
* optionally, lock the layer containing the image and create a new layer to work in;
* then do the following (the default _colors_ here can be changed in the export dialog):
    + trace the scale bar in _blue_, making a note of the distance
      this represents,
    + trace an orientation feature in _green_ (eg a North arrow, from S to N),
    + trace the desired survey traverse lines in _red_,
    + adjust the positions of nodes which are supposed to represent the same
      survey station until they are coincident (within the tolerance);
* optionally save the Inkscape file to preserve metadata;
* then do Extensions &rarr; Export &rarr; Export drawing to .svx file&hellip; 

In the subsequent dialog box, under the Parameters tab:

* an existing directory should be selected;
* the output `.svx` file should be selected from one of the options;
* then specify:
    + the length of scalebar line (in m);
    + the bearing of orientation line (in degrees);
    + the tolerance to equate stations (in m);
* optionally restrict export to a named layer;
* click on Apply.

A box should appear reporting that the `.svx` file has been generated
successfully.  If the conversion encounters errors, they are similarly
reported.  A succesfully generated `.svx` file is immediately ready
for processing by survex.

Notes:

1. The orientation and scalebar lines are picked up irrespective of
the layer selection.  Be careful not to get the colors of the
orientation and scalebar lines mixed up! There's no other way to tell
them apart: the conversion step cannot know the difference, and no
warning or error will be raised.

2. Path names in Inkscape can be set by Object &rarr; Object properties&hellip; 

3. If survex complains with an error
'Survey not all connected to fixed stations', then it is most likely a
pair of supposedly coincident survey stations are not close enough
together.  To diagnose this:
    + increase the tolerance until Survex no longer complains and the
    `.svx` file processes properly;
    + open the `.svx` file in a text editor and examine the list of
    `*equate` commands to see which stations were too far apart;
    + return to Inkscape and fix the problem.

4. It is suggested that magnetic N _not_ be corrected for using the
'bearing' setting in the Parameters tab.  Instead one can add a
`*calibrate declination` line by hand to the top of the survex file,
where the angle is positive for declination W. The [NOAA
website](http://www.ngdc.noaa.gov/geomag-web/ "NOAA geomagnetic
calculators") can be consulted to obtain declination data for a given
location and year.  Alternatively (and better) the declination can be
corrected automatically using `*cs` commands and a `*declination auto`
command (with a `*date`).  The design choice to export legs as `tape` and `compass`
readings, rather than as cartesian changes in easting and northing,
was made precisely to accommodate this.

5. Depth information can be added by hand by editing the `.svx` file.
A convenient way to do this is to change the survey data type to
`*data cylpolar from to tape compass depthchange`.  The final column
(which originally contained zero `clino` entries) can be edited to
reflect the depth change between survey stations, whilst preserving
the `tape` and `compass` entries which are presumably correct if taken
from a drawn-up survey in plan view.

6. A large survey can be dealt with by partitioning the
(poly)lines into different, named layers, keeping the same scale bar
and orientation line, but generating a different survex files for each
named layer.  These survex files can be stitched together using a
master file as illustrated below. Some hand editing has to be done to
match up the corresponding stations in the different survey data
files and it may be necessary to export these stations through
the `*begin` and `*end` blocks in each file.

7. Where it's not obvious what the scale bar represents or the units
conversion I often find it convenient to add a note in the form of a
text block to the Inkscape `.svg` file as in the examples below. In a
similar vein one can add an arrow to the _end_ of the orientation line
to affirm the direction, also done in the examples below.  This
doesn't affect the conversion.

### Examples

![Inkscape: `loneranger_cpcj6-2.png` plus traced survey lines.](loneranger_cpcj6-2_inkscape.png "Lone Ranger Series from CPC J vol 6(2)")

The file `loneranger_cpcj6-2.svg` is a tracing of a survey of the Lone
Ranger series in Link Pot (Easegill) where the PNG image
(`loneranger_cpcj6-2.png`) &ndash; originally published in CPC Journal 6(2)
&ndash; is taken from [CaveMaps](http://cavemaps.org/ "CaveMaps home
page").  The scale line end-end distance is 30 m, so 'Length of
scale line (in m)' in the Parameters tab should be set
to 30.0. 

![Inkscape: `far_country_ulsaj89.png` plus traced survey lines.](farcountry_ulsaj89_inkscape.png "Far Country from ULSA J 89")

Similarly, `farcountry_ulsaj89.svg` is a tracing of a survey of Far
Country in Gaping Gill where the PNG image (`farcountry_ulsaj89.png`)
&ndash; originally published in the ULSA '89 Journal &ndash; is likewise taken from
[CaveMaps](http://cavemaps.org/ "CaveMaps home page").  In this case
the scale line end-end distance is 200 ft, so the 'Length of scale
line (in m)' in the Parameters tab would be set to
60.96.  To get an idea of the work involved here, the generated Survex
file contains 176 survey stations, joined by 180 legs, with a total
length of around 1.5km of passage: it took less than 30 mins of
drawing in Inkscape to do.

#### Multiple layers

The `loneranger.svg` tracing can also be used to illustrate the use of
named Inkscape layers to break a survey into smaller pieces.  The
section from Matchbox aven to Tonto aven has been placed in a layer
named `matchbox`, and the remaining passage beyond Tonto aven in a
layer named `silverstream`.  Thus the survex files `matchbox.svx` and
`silverstream.svx` can be generated by exporting _twice_, using the
option in the Parameters tab in the export dialogue to restrict export
to each of these named layers in turn, taking the `.svx` file names
from the selected layer name. These survex files can each be processed
to a `.3d` file individually but to stitch them together we note that
station `path4288.8` in `matchbox.svx` should equate to station `path4290.0` in
`silverstream.svx`.  Hence the following short survex file will do the job:
```
*include matchbox
*include silverstream
*equate matchbox.path4288.8 silverstream.path4290.0
```
As it stands this doesn't quite work because we have not yet exported
these stations from the underlying survex blocks.  This has to be done
by hand: in `matchbox.svx`, add station 8 to the list of stations
exported from the `*begin path4288` block and add `*export path4288.8`
just below the top level `*begin matchbox` statement (both are needed,
as stations must be exported from each layer in turn).  Similarly in
`silverstream.svx` add station 0 to the list of stations exported from
the `*begin path4290` block and add `*export path4290.0` just below
the top level `*begin silverstream`.  Then one should be able to
process the above survex file to a combined `.3d` file.

### Georeferencing

Georeferencing refers to assigning a co-ordinate system to a map, in
this case for example to a scanned hard copy of a survey.  The actual
steps require identifying so-called Ground Control Points (GCPs),
which are identifiable features on the map for which actual
co-ordinates are known.  If the survey has a grid, or multiple
entrances, these can be used.  Frequently though the survey may only
have one entrance, and just a scale bar and North arrow.  In this case
one can use the survex export plugin to generate co-ordinates for
additional GCPs in the cave.  To do this one can either trace over the
passages and export the survex file, or more simply trace a fake
centerline which simply connects the extra GCPs to the entrance.
Check the generated `.svx` file can be processed, and then add a
`*fix` command to fix the entrance GCP to the known co-ordinates.
Processing this file  allows you
to extract the co-ordinates of the GCPs.

![Inkscape: `mossdale_ulsaj89.png` plus artifical survey lines.](mossdale_ulsaj89_inkscape.png "Mossdale Caverns from ULSA J 89")

For example suppose one wanted to georeference the ULSA 1989 Mossdale
survey, which is included here as `mossdale_ulsaj89.png`.  The
original of this was downloaded from [CaveMaps](http://cavemaps.org/
"CaveMaps home page").  This version has some material cropped out and
has been reduced to a binary (2-color) image.  The image is imported
into inkscape and the scale bar (500ft = 152.4m) and North arrow
traced (conveniently, the survey uses true North, so magnetic
declination need not be corrected).  To georeference, the simplest
approach is to add a single line connecting the entrance to a distant
identifiable feature in the cave, for example the small chamber shown
at the end of the Stream End Cave passage.  This line will be exported
as the survex centerline and the two stations will be our GCPs.  The
resulting inkscape drawing is included here as `mossdale_ulsaj89.svg`.
The exported survex file, modified as described below, is
`mossdale_ulsaj89.svx`.

We now need to establish the co-ordinates of the entrance, as the
first GCP.  To do this one can of course make a site visit with a GPS,
or perhaps more conveniently make a virtual site visit using
[MagicMap](http://www.magic.gov.uk/magicmap.aspx "Magic Map") website
and use the 'Where am I?' option to find the entrance is at (E, N) =
(401667, 469779).  This is the full 12-figure National Grid Reference
(NGR).  The 6-figure NGR SE 016697 given on the survey is correct of
course, but as it locates the entrance only to within a 100m square
it's not really accurate enough.

These entrance co-ordinates are added to the survex file together with
a a couple of `*cs` commands to georeference the same: choosing here
to `*fix` the entrance using a 10-figure NGR in the Ordnance Survey SE square,
and specifying the output co-ordinate reference system* (CRS) to be
EPSG:27700 (OSGB36 British National Grid) for the fully numeric NGR.  This may seem overkill but it
gets the CRS meta-data into the `.3d` file in a form suitable for
onward processing.  Also I have adopted the convention of equating the
entrance to a new station named `entrance` and fixing that.  Finally,
the entrance altitude (1400ft = 425m) has been added, although
irrelevant for present purposes.  
*Also known as a 'spatial reference system' (SRS).

Thus the final file (`mossdale_ulsaj89.svx`) contains
```
*cs OSGB:SE
*cs out EPSG:27700

*fix entrance 01667 69779 425
*entrance entrance
*equate entrance mossdale_ulsaj89.0

*begin mossdale_ulsaj89

*data normal from to tape compass clino

0   1   1383.460  112.7 0

*end mossdale_ulsaj89
```
Note there is no inner `*begin` and `*end` for the path as only one
path is exported.  Also it doesn't seem necessary to export the station out of the `*begin` / `*end` block.

On processing by `cavern` and `3dtopos` the result
is
```
( Easting, Northing, Altitude )
(401667.00, 469779.00,   425.00 ) entrance
(401667.00, 469779.00,   425.00 ) mossdale_ulsaj89.0
(402943.29, 469245.11,   425.00 ) mossdale_ulsaj89.1
```
(saved as `mossdale_ulsaj89.pos`).  The two entries give the
co-ordinates of the GCPs in the EPSG:27700 CRS and we can now
proceed to georeference the image file, using for example [QGIS](http://www.qgis.org/ "QGIS website").
The final result, here provided
as `mossdale_ulsaj89.tiff` in [GeoTIFF](https://en.wikipedia.org/wiki/GeoTIFF "GeoTIFF on Wikipedia") format, can be
directly imported into a GIS platform such as [QGIS](http://www.qgis.org/ "QGIS website"), and superimposed on other mapping data, Google
satellite imagery, or the Environment Agency LIDAR data where available, for example.

Since it is also georeferenced (by the `*cs` commands) the survex
centreline data can also be imported into QGIS using
a [QGIS plugin](https://github.com/patrickbwarren/qgis-survex-import) or a
[QGIS3 plugin](https://github.com/patrickbwarren/qgis3-survex-import).
The combined result, superimposed on an [Open Street Map](https://www.openstreetmap.org/) background, is here:

![QGIS3: `mossdale_ulsaj89.tiff` plus artificial survey line and Open Street Map data](mossdale_ulsaj89_qgis3.png "Mossdale Caverns from ULSA J 89 plus Open Street Map data.")

### Copying

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see
<http://www.gnu.org/licenses/>.

### Copyright

This program is copyright &copy; 2015, 2020, 2021 Patrick B Warren.
Survey copyrights &copy; are retained by original copyright holders.
