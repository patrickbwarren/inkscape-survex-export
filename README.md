## NEWS (June 13, 2015)

Good progress is being made with converting this tool into an Inkscape
extension: you might want to wait until this is done.  Mostly this
involves rewriting the code in python, and wiring it into the Inkscape
extension protocol.

## Survey data reconstruction

The main tool here is a perl script `reconstruct.pl` to reconstruct a
[survex](http://survex.com/ "The Survex Project home page") data file
from path data in an SVG file.  A typical workflow using
[Inkscape](https://inkscape.org/ "Inkscape home page") to prepare the
SVG file is described below.

For Windows, the perl script has been verified to run with [ActivePerl
for Windows](http://www.activestate.com/activeperl "ActivePerl home page"):
install ActivePerl and run the script from within a Command
Prompt window in the directory containing the SVG file (a "DOSbox" in
old terminology).

### Usage

`perl reconstruct.pl [opts] myfile.svg` (send output to terminal stdout)  
`perl reconstruct.pl [opts] myfile.svg > myfile.svx` (capture in a file)

Options `[opts]`:

* `--name=<name>` : (re)name top level `*begin` and `*end` block;
* `--scale=<length>` : gives the length of the scale bar (default 100m);
* `--bearing=<degrees>` : gives the bearing of the orientation line (default 0);
* `--tol=<tolerance>` : the tolerance in m (default 0.2) to equate stations;
* `--layer=<name>` : generate traverses only for paths belonging to that layer;
* `--extra` : adds extra information to the survex output as comments.

Of these options, `--scale` almost certainly has to be set unless the
scale bar is exactly 100m.

As indicated, the generated survex file is sent to stdout (terminal
output), but can be sent to a file instead using the redirection `>`
operator.

To read from stdin use `-` instead of a file name. This can be useful
on [unix](http://en.wikipedia.org/wiki/Unix "Wikipedia") or other
systems which support
[pipelines](http://en.wikipedia.org/wiki/Pipeline_%28Unix%29
"Wikipedia").

Usually the SVG file will be generated by tracing over a survey using
Inkscape as described below.  The following conventions are observed:

* red poly-line paths are converted to traverses in the survex file;
* a single green line path represents the orientation (default S to N);
* a single blue line path represents the scale bar;
* paths of any other color are ignored.

Traverses generated from red poly-lines are captured in separate
`*begin` and `*end` blocks in the survex file.  If an Inkscape layer
is specified by name (using the option below), then only those paths
belonging to that layer are included (the orientation and scale bar
are picked up irrespective of the layer).  The SVG path id is used for
the block name, so traverses can be matched up to paths in
Inkscape. The survey as a whole is wrapped in a top level `*begin` and
`*end` block with a name derived from the SVG file name (or the named
layer, or set as an option).

Within each traverse, survey legs are generated in the format  
`*data normal from to tape compass clino`  
The `from` and `to` stations are generated automatically.  The `tape`
length is generated using the scale bar line as reference (the true
length of the scale bar being specified as an option).  The `compass`
bearing is generated using the orientation line as reference (the true
orientation can be specified as an option if it is not S to N).  The
`clino` reading is set to zero.

Survey stations that are within a certain distance of each other (the
tolerance can be set as an option) are given as an `*equate` list at
the start.  Stations which feature in the `*equate` list are
automatically exported out of the underlying `*begin` and `*end`
block by the appropriate `*export` commands.  

## Workflow

A typical workflow using Inkscape might be as follows:

* start a new Inkscape document with (at least) two layers;
* import (link or embed) a scanned survey as an image in the bottom
  layer, and lock that layer (the visibility of this layer can be
  toggled to check on progress with tracing the survey);
* working in the next layer up:
  * trace the scale bar in _blue_, making a note of the distance
  this represents,
  * trace an orientation feature in _green_ (eg a N arrow),
  * trace the desired survey traverse lines in _red_,
  * adjust the positions of nodes which are supposed to represent the same
  survey station until they are coincident (within the tolerance);
* save the SVG file and process with the following command (where `XXX` is
  the distance represented by the scale bar)  
  `reconstruct.pl --scale=XXX myfile.svg > myfile.svx`
* the resulting survex file should just process with `cavern`
  (or right-click and process in Windows).

Notes:

1. Orientation features which are not N arrows can be used, and the
bearing that is represented can be set using the `--bearing=<degrees>`
command line option.  It is probably good practice to add by hand a comment
indicating what was used for the orientation line (eg grid N or mag N)

2. However it is not recommended to correct magnetic N this way;
instead add a `*calibrate declination <angle>` line by hand to the top
of the survex file, where the angle is positive for declination W. The
[NOAA website](http://www.ngdc.noaa.gov/geomag-web/
"NOAA geomagnetic calculators") can be used to obtain declination data
for a given location and year.  The design choice to export legs as
`tape` and `compass` readings, rather than as cartesian changes in
easting and northing, was made precisely to accommodate this problem
of the magnetic declination.

3. The automatically generated `*equate` list may contain superfluous
entries if more than two path nodes are at the same position.  The
fastidious can correct this by hand afterwards but it doesn't affect
the processing of the survex file by `cavern`.

4. Inkscape layers can be used to restrict which paths are converted
into survey traveses in the survex file, if the layer name is
specified as an option.  This means one can work with a large survey,
keeping the same scale bar and orientation line, but generating a
different survex files for each named layer.  The top level `*begin` and
`*end` block is given the name of the layer (if not specified
explicitly as an option) rather than a name derived from the file
name.  These survex files can be stitched together using a master file
as illustrated below.

5. To stitch together multiple files, one has to identify
corresponding stations in the survey data.  However `cavern` will
complain if these stations are not properly exported, and it is
necessary to edit by hand the data files to export the necessary
stations through all the `*begin` and `*end` abstraction layers.

6. Pitches and other purely vertical legs can be added of course, by
hand.

4. Additional SVG features are ignored, and a missing linked image
file is no problem.

7. Finally, in preparing the SVG file using Inkscape, care should be
taken to avoid unusual directives in the `d` attribute which defines a
path.  The `d` attribute should start with (lowercase) `m` directive
and just feature a list of relative moves, but sometimes spurious `M`
and `L` directives can arise if the path has been constructed
non-sequentially.  Paths containing unexpected directives will be
rejected (with a warning) by the `reconstruct.pl` script.  These paths
can be inspected and the spurious directives removed, either by
opening the SVG file in a text editor, or by using the XML editor in
Inkscape itself.  Removing directives usually makes the path nodes
jump around though.

## Example

The file `loneranger.svg` shows traverses traced on top of a PNG image
of the Lone Ranger series (Link Pot, Easegill) survey, taken from
[CaveMaps](http://cavemaps.org/ "CaveMaps home page"), originally
published in CPC Journal 6(2).  The PNG image is linked in this file.
The scale bar line end-end distance is 30m so the SVG file is
processed with

```
perl reconstruct.pl --scale=30 loneranger.svg > loneranger.svx
```

This can be processed by `cavern` to a `.3d` right away, but to finish
off the magnetic declination would be inserted as described above, and
any superfluous `*equate`s can be commented out.

In fact `loneranger.svg` can also be used to illustrate the use of
named Inkscape layers to break a survey into smaller pieces since the
section from Matchbox aven to Tonto aven is in a layer named
"matchbox", and the remaining passage beyond Tonto aven is in a layer
named "silverstream".  Thus `loneranger.svg` can also be processed
into _two_ survex files with the following commands:

```
perl reconstruct.pl --scale=30 --layer=matchbox loneranger_layered.svg > matchbox.svx
perl reconstruct.pl --scale=30 --layer=silverstream loneranger_layered.svg > silverstream.svx
```

This will generate the two survex files `matchbox.svx` and
`silverstream.svx` (by convention, the survex file name should be
chosen to match the name of the top level `*begin` and `*end` block,
here set by the layer name).  Each of these survex files can be
processed with `cavern` and viewed with `aven`.  To stitch them
together we note that Tonto aven is station 8 in `path4288` in
`matchbox.svx`, and is also station 0 in `path4290` in
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

---

Copyright &copy; 2015 Patrick B Warren.

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
