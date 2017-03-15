# gethigal
A selenium webscraper for automated download of the [Hi-GAL DR1](http://adsabs.harvard.edu/abs/2016A%26A...591A.149M) data products.

#### Dependencies
* Python 3.x
* Firefox with `geckodriver`
* `selenium`
* `astropy`

#### Drawbacks
* Some manual interaction with Firefox is still required
* Default download directory has to hacked around

#### Installation
To clone and install `gethigal` locally:

```bash
git clone https://github.com/vlas-sokolov/gethigal.git
cd gethigal
pip install .
```

#### Example use

The following code snippet downloads the Hi-GAL maps in a 15 arcminute radius around the IRDC G035.39-00.33:

```python
import os
import astropy.units as u
import astropy.coordinates as c
from gethigal.requestform import RequestForm

home_dir = os.path.expanduser('~')

radius = 15*u.arcmin
skycoord_g035_39 = c.SkyCoord(284.2875*u.deg, 2.1294*u.deg, frame = 'fk5')

# Opens a Firefox session with "save file" pop-ups
getter = RequestForm(skycoord_g035_39, radius, submit = True)

# After the files are saved, moves them to a designated directory
getter.fix_download_loc(os.path.join(home_dir, 'Downloads/'), 'data/',
                        globber = "HIGAL*354*.fits", lay_low = True)

# Quits the browser session
getter.quit()
```
