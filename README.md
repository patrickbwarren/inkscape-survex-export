## Survey data reconstruction

The tool here adds an [Inkscape](https://inkscape.org/ "Inkscape home
page") option to save a drawing to a [Survex](http://survex.com/ "Survex
home page") (`.svx`) file.  A typical workflow starting from a
scanned drawn-up survey image is described below.  Use-cases might
include:

* producing a plausible length estimate for a drawn-up survey;
* generating a skeleton from an existing drawn-up survey, to hang data
off in a resurvey project.

A couple of example surveys (Inkscape traced drawings) are also included.

### Installation

Copy the files `agr_import.py` and `agr_import.inx` into your local
Inkscape extension folder (eg `$HOME/.config/inkscape/extensions/` on
unix, or `%APPDATA%\inkscape\extensions\` on Windows).  That's it &ndash;
there are no additional dependencies and this should work on all
platforms.

### Usage

In Inkscape, the option to save to a Survex (`*.svx`) file should now
appear under 'File &rarr; Save As&hellip;' or 'File &rarr; Save a
Copy&hellip;'.  If selected this brings up a dialogue box, with:

* in the 'Parameters' tab:
    + length of scale line (in m);
    + bearing of orientation line (in degrees);
    + tolerance to equate stations (in m);
    + an option to restrict conversion to a named layer;
* in the 'Colors' tab, options to change the default line colors;
* in the 'Help' tab, a reminder of the expected drawing conventions.

Usually the drawing will be made by tracing over a scannned image of a
drawn-up survey.  The following conventions are observed:

* by default, all red (poly)lines are converted to traverses in the survex file;
* by default, a single green line line determines the orientation (default S to N);
* by default, a single blue line line determines the scale (eg from the scale bar);

Lines of any other color are ignored, as are other drawing objects.
The default colors can be changed in the 'Colors' tab in the export
dialogue box.  If an Inkscape layer is specified by name in the
'Parameters' tab, then only those (red) (poly)lines belonging to that
layer are exported (the orientation and scale bar are picked up
irrespective of the layer).

Traverses generated from (poly)lines are captured in separate `*begin`
and `*end` blocks in the survex file.  The Inkscape path id is used for the
block name, so traverses can be matched up to paths in Inkscape. The
survey as a whole is wrapped in a top level `*begin` and `*end` block
with a name derived from the Inkscape docname (or, if export is
restricted to a given layer, the name of that layer).

Within each traverse, survey legs are generated in the format

`*data cylpolar from to tape compass depthchange`

In this format:

* The `from` and `to` stations are generated automatically.

* The `tape` length is generated using the scale line as reference.
It will usually be traced over a scale bar in the survey.  The true
length that the scale line represents is specified in the 'Parameters'
tab in the export dialogue box.

* The `compass` bearing is generated using the orientation line as
reference.  It will usually be traced over a North arrow in the survey
(in the direction S to N).  If a North arrow is not used the true
bearing represented by the orientation line can be specified in the
'Parameters' tab in the export dialogue box.

* The `depthchange` reading is set to zero since usually the tracing will be
made of a survey in plan view (hence the choice to use the `cylpolar`
format).  Depth information may subsequently be added by hand.

Survey stations that are within a certain distance of each other are
given as an `*equate` list at the start.  The distance tolerance to
select these is usually small (eg 0.2m) and can be adjusted in the
'Parameters' tab in the export dialogue box.  Stations which feature
in the `*equate` list are automatically exported out of the underlying
`*begin` and `*end` block by the appropriate `*export` commands.

### Workflow

A typical workflow using Inkscape might be as follows:

* start a new Inkscape document;
* import (link or embed) a scanned survey as an image and
  lock the layer that contains this image;
* create a new layer above this layer to work in:
    + trace the scale bar in _blue_, making a note of the distance
      this represents,
    + trace an orientation feature in _green_ (eg a North arrow, from S to N),
    + trace the desired survey traverse lines in _red_,
    + adjust the positions of nodes which are supposed to represent the same
      survey station until they are coincident (within the tolerance);
* save the Inkscape file to preserve metadata;
* do File &rarr; Save a Copy&hellip;, select 'Survex file (`*.svx`)', choose a file name, and click on Save;
* fill in the options in the 'Parameters' tab with (at least) the length of the scale bar, click on OK;
* the resulting survex file is processable to a `.3d` file (eg with `cavern` in unix,
  or by right-clicking and selecting 'Process' in Windows).

Notes:

0. 'File &rarr; Save a Copy&hellip;' is preferred to 'File &rarr; Save
As&hellip;', since it prevents Inkscape from thinking that the actual
Inkscape drawing is of file type `.svx`.

1. If on processing the `.svx` file, Survex complains with an error
'Survey not all connected to fixed stations', then it is most likely a
pair of supposedly coincident survey stations are not close enough
together (they may have been overlooked).  To diagnose this:
    + increase the tolerance until Survex no longer complains and the `.svx` file processes properly;
    + open the `.svx` file in a text editor and examine the list of `*equate` commands to see which stations were too far apart;
    + return to Inkscape and fix the problem.

2. The automatically generated `*equate` list may contain superfluous
entries if more than two path nodes are at the same position.  The
fastidious can correct this by hand afterwards but it doesn't affect
the processing of the survex file.

3. It is not recommended to correct magnetic N using the 'bearing'
setting in the 'Parameters' tab in the export dialogue box.  Instead
add a `*calibrate declination <angle>` line by hand to the top of the
survex file, where the angle is positive for declination W. The [NOAA
website](http://www.ngdc.noaa.gov/geomag-web/ "NOAA geomagnetic
calculators") can be used to obtain declination data for a given
location and year.  The design choice to export legs as `tape` and
`compass` readings, rather than as cartesian changes in easting and
northing, was made precisely to accommodate this.

4. A large survey can be dealt with by partitioning the (red)
(poly)lines into different, named layers, keeping the same scale bar
and orientation line, but generating a different survex files for each
named layer.  These survex files can be stitched together using a
master file as illustrated below. To facilitate this, the top level
`*begin` and `*end` block is given the name of the layer rather than a
name derived from the docname.  However some hand editing still has to
be done to match up the corresponding stations in the different survey
data files: in particular it is necessary to export these stations
through the `*begin` and `*end` abstraction layers.

### Examples

The file `loneranger_cpcj6-2.svg` is a tracing of a survey of the Lone
Ranger series in Link Pot (Easegill) where the PNG image
(`loneranger_cpcj6-2.png`) &ndash; originally published in CPC Journal 6(2)
&ndash; is taken from [CaveMaps](http://cavemaps.org/ "CaveMaps home
page").  The scale line end-end distance is 30 m, so the 'length of
scale line (in m)' parameter in the export dialogue box would be set
to 30.0.

Similarly, `farcountry_ulsaj89.svg` is a tracing of a survey of Far
Country in Gaping Gill where the PNG image (`farcountry_ulsaj89..png`)
&ndash; originally published in ULSA '89 Journal &ndash; is likewise taken from
[CaveMaps](http://cavemaps.org/ "CaveMaps home page").  In this case
the scale line end-end distance is 200 ft, so the 'length of scale
line (in m)' parameter in the export dialogue box would be set to
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

This program is copyright &copy; 2015 Patrick B Warren.
