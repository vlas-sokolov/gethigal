import astropy.units as u
import astropy.coordinates as c
from astroquery.vizier import Vizier

import sys
if not sys.version.startswith('3'):
    raise NotImplementedError('Not compatible with Python 2.x versions!')

# get this first: https://github.com/vlas-sokolov/gethigal
from gethigal.requestform import RequestForm

def R2006_skycoords(irdc):
    """ Coordinates of an IRDCs in Rathborne et al. 2006 """
    irdcs = Vizier.get_catalogs("J/ApJ/641/389/table2")[0].to_pandas()
    irdcs.RAJ2000 = irdcs.RAJ2000.apply(lambda s: s.decode().replace(' ', ':'))
    irdcs.DEJ2000 = irdcs.DEJ2000.apply(lambda s: s.decode().replace(' ', ':'))
    irdc_skcds = c.SkyCoord(irdcs.RAJ2000, irdcs.DEJ2000,
                            unit = (u.h, u.deg), frame = 'fk5')

    skcd = irdc_skcds[(irdcs.MSXDC == irdc).values][0]
    return skcd

g35_39_skcd = R2006_skycoords(b'G035.39-00.33')
radius = 30*u.arcmin

getter = RequestForm(g35_39_skcd, radius, submit = True)

import os
home_dir = os.path.expanduser('~')
getter.fix_download_loc(os.path.join(home_dir, 'Downloads/'), 'data/',
                        globber = "*354*.fits", lay_low = True)

getter.quit()
