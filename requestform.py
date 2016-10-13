"""
Contains the RequestForm class, designed to interact with
the two layers of the Hi-GAL data web request form.
"""
from selenium.webdriver import FirefoxProfile, Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as ec
import astropy.units as u
from astropy import log
import os

def get_firefox_profile(data_path):
    """
    Because selenium on its own isn't so good at web scraping.
    """
    # FIXME: does not work properly with selenium '3.0.0.b3'
    fp = FirefoxProfile()
    fp.set_preference('browser.download.folderList', 2)
    fp.set_preference('browser.download.manager.showWhenStarting', False)
    fp.set_preference('browser.download.dir', data_path)
    fp.set_preference('browser.helperApps.neverAsk.saveToDisk',
                      'application/download')
    return fp


class RequestForm(Firefox):
    """
    Manipulate firefox session through selenium, connect to the HiGal
    DR1 web query form, fill it from a given SkyCoord and search radius,
    and save the Herschel FITS files locally.
    """

    def __init__(self, skcd = None, radius = None, submit = False,
                 local_dir = '', url = None):
        """
        Parameters
        ----------
        skcd : astropy.coordinates.SkyCoord
            The search center. Can be either 'fk5' or 'galactic' frame.
        radius : astropy.units.quantity.Quantity
            Search radius.
        submit : bool
            If true, send the search request to the server.
            Basically, clicks the "Seach" button.
        local_dir : string
            Relative path to a folder for the output data. WIP.
            Depending on the version combo of selenium / firefox, might not
            make any difference - newer versions of firefox are quite strict
            with external python modules messing up the user profile settings.
        url : string
            The URL of the javascript web service for DR1 data.
            Defaults to "http://tools.asdc.asi.it/HiGAL.jsp".
        """
        fp = get_firefox_profile(os.getcwd() + '/' + local_dir)
        super().__init__(firefox_profile=fp)
        self.band_to_idx = dict(HIGAL_BLUE=4047, HIGAL_RED=4051,
                HIGAL_PSW=4050, HIGAL_PMW=4049, HIGAL_PLW=4048)
        url = url or 'http://tools.asdc.asi.it/HiGAL.jsp'
        log.info('Loading a webpage from ({}).'.format(url))
        self.get(url)
        if radius:
            self.set_radius(radius)
        if skcd:
            self.set_coordsys(skcd)
            self.input_coords(skcd)
        if submit:
            self.submit()
            log.info('Waiting for the result page to load...')
            switched_gears = lambda x: 'HiGALSearch' in x.current_url
            WebDriverWait(self, 60, 0.5).until(switched_gears)
            self.download_fits()

    def __repr__(self):
        return 'Running [{}] on ({})'.format(self.title, self.current_url)

    def set_coordsys(self, skcd):
        """
        For a given SkyCoord, checks the corresponding coordinate system box.
        """
        frame_to_chbox_name = {'galactic': 'coordsTypeLB',
         'fk5': 'coordsTypeRADEC'}
        chbox_id = frame_to_chbox_name[skcd.frame.name]
        log.info('Setting the coordinate system to {}'.format(skcd.frame.name))
        self.coord_chbox = self.find_element_by_id(chbox_id)
        self.coord_chbox.click()

    def input_coords(self, skcd):
        """
        Get a WebElement with coordinate input and fill in
        the sky coordinate string from a SkyCoord instance.
        """
        self.coord_input = self.find_element_by_id('coordobjc')
        log.info('Setting the coordinates to {}'.format(skcd.to_string()))
        self.coord_input.clear()
        self.coord_input.send_keys(skcd.to_string())

    def set_radius(self, radius):
        """
        Inputs search radius (in arcmin) into the javascript form.
        """
        if type(radius) is not u.quantity.Quantity:
            log.warning("radius doesn't have units, assiming arcminutes!")
            radius = radius * u.arcmin
        radius_arcmin = '{}'.format(radius.to(u.arcmin).value)
        self.radius_input = self.find_element_by_id('radiusInput')
        self.radius_input.clear()
        self.radius_input.send_keys(radius_arcmin)

    def submit(self):
        """
        Not the most elegant way to click the "Search"
        button, but hey it's the way we've got.
        """
        submit_xpath = '//div[2]/form/table/tbody/tr[4]/td/input'
        self.search_button = self.find_element_by_xpath(submit_xpath)
        log.info('Submitting the job...')
        self.search_button.click()

    def get_downloader(self, band):
        """
        Returns a `mapDownload` web element for a given Herschel band
        """
        idx = self.band_to_idx[band]
        hideimg_id = 'ckHideImg_{}'.format(idx)
        hide_img = self.find_element_by_id(hideimg_id)
        parent = hide_img.find_element_by_xpath('..')
        download = parent.find_element_by_id('mapDownload')
        setattr(self, 'download_{}'.format(band), download)
        return download

    def download_fits(self, bands = None, timeout = 60,
                      interval = 0.5, post_nap = 3):
        """
        Attemps to click on all Herschel image downloads
        """
        test_id = 'mapDownload'
        try:
            log.info('Waiting for the clickable elements to show up...')
            WebDriverWait(self, timeout, interval).until(
                    ec.presence_of_element_located((By.ID, test_id)))
        except TimeoutException:
            log.error('timeout (>{} s) for the `{}` element to load'
                      ' on [{}]'.format(timeout, test_id, self.current_url))
            return

        log.info('Downloading the FITS files.')
        bands = bands or self.band_to_idx.keys()
        for band in bands:
            downloader = self.get_downloader(band)
            downloader.click()
