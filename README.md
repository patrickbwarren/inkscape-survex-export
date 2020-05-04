## Survey data reconstruction

* _Use v1.1 of this plugin for Inkscape 0.92_
* _Work in progress to port to Inkscape 1.0_

The tool here adds an [Inkscape](https://inkscape.org/ "Inkscape home
page") option to save a drawing to a [Survex](http://survex.com/ "Survex
home page") (`.svx`) file.  A typical workflow starting from a
scanned drawn-up survey image is described below.  Use-cases might
include:

* producing a plausible length estimate for a drawn-up survey;
* georeferencing a drawn-up survey (see below);
* generating a skeleton from an existing drawn-up survey, to hang data
off in a resurvey project;
* giving 'armchair cavers' something useful to do.

A couple of example surveys (Inkscape traced drawings) are also included.

### Installation

Copy the files `svx_export.py` and `svx_export.inx` into your local
Inkscape extension folder (eg `$HOME/.config/inkscape/extensions/` on
unix, or `%APPDATA%\inkscape\extensions\` on Windows).  

That's it &ndash;
there are no additional dependencies and this should work on most
platforms.  In particular it has been tested to work with Inkscape 0.91 (r13725), on both
Linux and Windows.

### Usage

Usually the drawing will be made by tracing over a scannned image of a
drawn-up survey.  The following conventions are observed:

* by default, all red (poly)lines are converted to traverses in the survex file;
* by default, a single green line line determines the orientation (default S to N);
* by default, a single blue line line determines the scale (eg from the scale bar);

Lines of any other color are ignored, as are other drawing objects.
The default colors can be changed (see below), for example to red-blue-black 
if red-green-blue gives problems.

In Inkscape, the option to save to a Survex (`*.svx`) file should
appear under 'File &rarr; Save As&hellip;' or 'File &rarr; Save a
Copy&hellip;'.  This brings up a dialogue box, with:

* in the 'Parameters' tab:
    + length of scale line (in m);
    + bearing of orientation line (in degrees);
    + tolerance to equate stations (in m);
    + an option to restrict conversion to a named layer;
* in the 'Colors' tab, options to change the default line colors;
* in the 'Help' tab, a reminder of the expected drawing conventions.

If an Inkscape
layer is specified by name in the 'Parameters' tab, then only those
(red) (poly)lines belonging to that layer are exported.  The
orientation and scale lines are picked up irrespective of the layer.

Traverses generated from (poly)lines are captured in separate `*begin`
and `*end` blocks in the survex file.  The Inkscape path id is used for the
block name, so traverses can be matched up to paths in Inkscape. The
survey as a whole is wrapped in a top level `*begin` and `*end` block
with a name derived from the Inkscape docname (or, if export is
restricted to a given layer, the name of that layer).

Within each traverse, survey legs are generated in the format

`*data normal from to tape compass clino`

In this format:

* The `from` and `to` stations are generated automatically.

* The `tape` length is generated using the scale line as reference,
which will usually be traced over a scale bar in the survey.  The true
length that the scale line represents is specified in the 'Parameters'
tab in the export dialogue box.

* The `compass` bearing is generated using the orientation line as
reference, which for example will be traced over a North arrow in the survey
(in the direction S to N).  If a North arrow is not used the true
bearing represented by the orientation line can be specified in the
'Parameters' tab in the export dialogue box.

* The `clino` reading is set to zero.

Survey stations that are within a certain distance of each other are
given as an `*equate` list at the start.  The distance tolerance to
select these is usually small (eg 0.2m) and can be adjusted in the
'Parameters' tab in the export dialogue box.  Stations which feature
in the `*equate` list are automatically exported out of the underlying
`*begin` and `*end` block by the appropriate `*export` commands.

The python script `svx_output.py` can also be used standalone at the
command line.  The required modules in the Inkscape global extensions
direcory should be made discoverable though: these are `inkex.py`,
`simplepath.py`, and `simplestyle.py`.  The simplest way is to copy
these `.py` files to the same directory that contains `svx_output.py`.
Command line options can be found by doing `./svx_output.py --help`.

### Workflow

A typical workflow using Inkscape might be as follows:

* start a new Inkscape document;
* import (link or embed) a scanned survey as an image;
* optionally, lock the layer containing the image and create a new layer to work in;
* then do the following:
    + trace the scale bar in _blue_, making a note of the distance
      this represents,
    + trace an orientation feature in _green_ (eg a North arrow, from S to N),
    + trace the desired survey traverse lines in _red_,
    + adjust the positions of nodes which are supposed to represent the same
      survey station until they are coincident (within the tolerance);
* save the Inkscape file to preserve metadata;
* do File &rarr; Save a Copy&hellip; and select 'Survex file (`*.svx`)';
* choose a file name and click on Save;
* in the dialogue box that appears, in the 'Parameters' tab, fill in at least the length of the scale line to correspond to the length of the traced scale bar;
* click on OK to generate the `.svx` file;

Notes:

1. 'File &rarr; Save a Copy&hellip;' is preferred to 'File &rarr; Save
As&hellip;', since it prevents Inkscape from thinking that the actual
Inkscape drawing is of file type `.svx`.

2. If Survex complains with an error
'Survey not all connected to fixed stations', then it is most likely a
pair of supposedly coincident survey stations are not close enough
together (they may have been overlooked).  To diagnose this:
    + increase the tolerance until Survex no longer complains and the `.svx` file processes properly;
    + open the `.svx` file in a text editor and examine the list of `*equate` commands to see which stations were too far apart;
    + return to Inkscape and fix the problem.

3. The automatically generated `*equate` list may contain superfluous
entries if more than two path nodes are at the same position.  The
fastidious can correct this by hand afterwards but it doesn't affect
the processing of the survex file.

4. It is suggested that magnetic N _not_ be corrected for 
using the 'bearing'
setting in the 'Parameters' tab.  Instead
add a `*calibrate declination <angle>` line by hand to the top of the
survex file, where the angle is positive for declination W. The [NOAA
website](http://www.ngdc.noaa.gov/geomag-web/ "NOAA geomagnetic
calculators") can be used to obtain declination data for a given
location and year.  The design choice to export legs as `tape` and
`compass` readings, rather than as cartesian changes in easting and
northing, was made precisely to accommodate this.

5. Depth information can be added by hand by editing the `.svx` file.
A convenient way to do this is to change the survey data type to
`*data cylpolar from to tape compass depthchange`.  The final column
(which originally contained zero `clino` entries) can be edited to
reflect the depth change between survey stations, whilst preserving
the `tape` and `compass` entries which are presumably correct if taken
from a drawn-up survey in plan view.

6. A large survey can be dealt with by partitioning the (red)
(poly)lines into different, named layers, keeping the same scale bar
and orientation line, but generating a different survex files for each
named layer.  These survex files can be stitched together using a
master file as illustrated below. To facilitate this, the top level
`*begin` and `*end` block is given the name of the layer rather than a
name derived from the docname (and by convention this should also be
the name of the `.svx` file).  Some hand editing has to be done to
match up the corresponding stations in the different survey data
files: in particular it is necessary to export these stations through
the `*begin` and `*end` blocks in each file.

### Examples

The file `loneranger_cpcj6-2.svg` is a tracing of a survey of the Lone
Ranger series in Link Pot (Easegill) where the PNG image
(`loneranger_cpcj6-2.png`) &ndash; originally published in CPC Journal 6(2)
&ndash; is taken from [CaveMaps](http://cavemaps.org/ "CaveMaps home
page").  The scale line end-end distance is 30 m, so 'Length of
scale line (in m)' in the 'Parameters' tab would be set
to 30.0.

Similarly, `farcountry_ulsaj89.svg` is a tracing of a survey of Far
Country in Gaping Gill where the PNG image (`farcountry_ulsaj89.png`)
&ndash; originally published in the ULSA '89 Journal &ndash; is likewise taken from
[CaveMaps](http://cavemaps.org/ "CaveMaps home page").  In this case
the scale line end-end distance is 200 ft, so the 'Length of scale
line (in m)' in the 'Parameters' tab would be set to
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
option in the 'Parameters' tab in the export dialogue to restrict
conversion to each of these named layers in turn.  (By convention, the
survex file name should be chosen to match the name of the top level
`*begin` and `*end` block, here set by the layer name.)  These
survex files can each be processed to a `.3d` file individually, but to
stitch them together we note that Tonto aven is station 8 in
`path4288` in `matchbox.svx`, and is also station 0 in `path4290` in
`silverstream.svx`.  Hence the following short survex file (here
called `combined.svx`) will do the job:

```
; combined.svx 
*include matchbox
*include silverstream
*equate matchbox.path4288.8 silverstream.path4290.0
```

As it stands this doesn't quite work because we have not yet exported
these stations from the underlying survex `*begin` and `*end` blocks.
This has to be done by hand: in `matchbox.svx`, add station 8 to the
list of stations exported from the `path4288` block, _and_ add a line
`*export path4288.8` just below the top level `*begin matchbox`
statement (both are needed, as stations must be exported from each
layer in turn).  A similar pair of edits is required in
`silverstream.svx`.  Then one should be able to process `combined.svx`
to a `.3d` file.

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

For example suppose one wanted to georeference the ULSA 1989 Mossdale
survey, which is included here as `mossdale_ulsaj89.png`.  The
original of this was downloaded from 
[CaveMaps](http://cavemaps.org/ "CaveMaps home page").  
This version has some material cropped out and
has been reduced to a binary (2-colour) image.  The image is imported into
inkscape and the scale bar (500ft = 152.4m) and North arrow traced
(conveniently, the survey uses true North, so magnetic declination
need not be corrected).  We then add a single line connecting the
entrance to a distant identifiable feature in the cave, for example
the small chamber shown at the end of the Stream End Cave passage.
This line will be exported as the survex centerline.
The resulting inkscape drawing is included here as `mossdale_ulsaj89.svg`.
The exported survex file, modified as described below, is `mossdale_ulsaj89.svx`.

We now need to establish the co-ordinates of the entrance, as the
first GCP.  To do this one can of course make a site visit with a GPS,
or perhaps more conveniently make a virtual site visit using
[MagicMap](http://www.magic.gov.uk/magicmap.aspx "Magic Map") website and
use the 'Where am I?' option to find the entrance is at
`(E, N) = (401667, 469779)`.
This is
the full 12-figure grid reference in the OSGB36 co-ordinate reference system.
The 6-figure NGR SE 016697 given on the survey
is correct of course, but as it locates the entrance only to within a
100m square it's not really accurate enough.  An alternative to using
Magic Map is to use Google Earth or Google Maps with satellite imagery
to find the WGS84 location of the entrance is `(N, W) = (54°7'26", 1°58'34")`.
These can then be converted to OSGB36 co-ordinates.

We add these entrance co-ordinates to the survex file which now contains
```
*begin mossdale_ulsaj89
*fix entrance 401667 469779 425
*entrance entrance
*equate entrance path4342.0

*data normal from to tape compass clino

*begin path4342
*export 0
  0   1 1383.46  113  0
*end path4342

*end mossdale_ulsaj89 
```
I have adopted the convention of exporting
the entrance (station `0` in `path4342`) out to the top level, and
equating it to a new station named `entrance`.  Also the altitude
(1400ft = 425m) has been added, although irrelevant for present purposes.  On processing by `cavern` and `3dtopos` the result
is
```
( Easting, Northing, Altitude )
(401667.00, 469779.00,   425.00 ) mossdale_ulsaj89.entrance
(401667.00, 469779.00,   425.00 ) mossdale_ulsaj89.path4342.0
(402940.48, 469238.44,   425.00 ) mossdale_ulsaj89.path4342.1
```
(saved as `mossdale_ulsaj89.pos`).  The last line gives the
co-ordinates of the GCP at the end of Stream End Cave.  We can now
proceed to georeference the survey, for example using [QGIS](http://www.qgis.org/ "QGIS website").  One point
to note is that the relevant co-ordinate system is
```
OSGB 1936 / British National Grid    EPSG:27700
```
It is the European Petroleum Survey Group (EPSG) number that
really identifies this.  The final georeferenced survey, here provided
as `mossdale_ulsaj89.tiff` in [GeoTIFF](https://en.wikipedia.org/wiki/GeoTIFF "GeoTIFF on Wikipedia") format, can be
directly imported into a GIS platform such as [QGIS](http://www.qgis.org/ "QGIS website"), and superimposed on Google
satellite imagery, or the Environment Agency LIDAR data, for example.

The survex centreline data can also be imported into a GIS platform by using
the `cad3d` survex tool to export the `.3d` file to `.dxf`.  The centreline in
this `.dxf` file can be extracted for example by running the following
[GDAL](http://www.gdal.org/ "GDAL website") command, which generates a
[GeoJSON](http://geojson.org/ "GeoJSON website") file:
```
ogr2ogr -f "GeoJSON" outfile.json infile.dxf -where "Layer='CentreLine'"
```

As an alternative to the full 12-figure OS grid reference, one
can use the more conventional NGR 10-figure grid reference
provided the co-ordinate
systems are specified in the `.svx` file.  For example, from our work above
the Mossdale entrance
is at NGR SE 01667 69779, and the following can be used
```
*cs OSGB:SE
*cs out EPSG:27700

*begin mossdale_ulsaj89
*fix entrance 01667 69779 425
*entrance entrance
*equate entrance path4342.0

*data normal from to tape compass clino

*begin path4342
*export 0
  0   1 1383.46  113  0
*end path4342

*end mossdale_ulsaj89 
```
Processing this file (here provided as `mossdale_ulsaj89.svx`)
by `cavern` and `3dtopos` gives the same result as above, but note
this may require a 
recent version of survex to handle the `*cs` commands.
The survex documentation is a bit vague on how to use the `*cs`
command so this is probably not the only way to do this.

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

This program is copyright &copy; 2015, 2020 Patrick B Warren.
