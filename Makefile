# This file is part of the Inkscape survex exporter plugin.

# This is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# Copyright (c) 2021 Patrick B Warren <patrickbwarren@gmail.com>.

# You should have received a copy of the GNU General Public License
# along with this file.  If not, see <http://www.gnu.org/licenses/>.

DOCS = README.pdf README.html
FIGS1 = loneranger_cpcj6-2_inkscape.png farcountry_ulsaj89_inkscape.png
FIGS2 = mossdale_ulsaj89_inkscape.png mossdale_ulsaj89_qgis3.png
FIGS = $(FIGS1) $(FIGS2)

default: $(DOCS)

README.html README.pdf: README.md $(FIGS)
	pandoc -s -o $@ $<

clean : 
	rm -f *~
