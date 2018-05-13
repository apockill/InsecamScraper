from time import sleep

from selenium.common.exceptions import \
    NoAlertPresentException, NoSuchElementException, TimeoutException
from selenium.webdriver import ChromeOptions
from selenium.webdriver import Chrome as Driver
from bs4 import BeautifulSoup


class InseCamCrawler:
    def __init__(self, driver_path, websites_txt):
        """
        :param profile_manager: A ProfileManager object with all profiles loaded already
        :param driver_path: The path to the browser driver that is being used for scraping
        :param config: A CrawlerConfig object
        """

        # Get the list of websites from the file
        self.websites = []
        with open(websites_txt, "r") as file:
            for line in file:
                line = line.replace('\n', '')
                self.websites.append(line)

        # Parameters
        self.driver_path = driver_path

        # Controls
        self.crawled_urls = []
        self.browser = None

    def __iter__(self):
        """ This runs in a new thread when crawler.run() is called """
        self._start_browser()

        # Start crawling each URL
        for url in self.websites:
            print("Starting Crawling on Seed: ", url)
            for ip in self._crawl_page(url):
                yield ip

        self._close_browser()

    def _crawl_page(self, url):

        if url in self.crawled_urls:
            print("Tried to crawl the same URL twice in one session", url)
            return

        self.crawled_urls.append(url)

        # Load the seed page
        html = self._load_page(url)
        if html is None:
            return

        while True:
            # Get IP's from this page, and yield them
            for ip in self._get_page_ips(self.browser.page_source): yield ip

            while True:
                # Load the next page
                try:
                    next_button = self.browser.find_element_by_link_text("»")
                    next_button.click()
                    break
                except NoSuchElementException:
                    print("Crawler: No more pages to click next at! Continuing...")
                    return
                except TimeoutException:
                    print("Crawler: Unable to click next. Waiting!")
                    sleep(5)
                    continue
                except Exception as e:
                    print("Crawler: SERIOUS ERROR: ", e, "exiting page")
                    return

    def _get_page_ips(self, html):
        page_ips = []
        soup = BeautifulSoup(html, "html5lib")
        imgs = soup.find_all("img", class_="thumbnail-item__img img-responsive")
        for img in imgs:
            page_ips.append(img["src"])
        return page_ips

    def _load_page(self, url):
        def dismiss_alerts():
            while True:
                try:
                    alert = self.browser.switch_to.alert
                    alert.accept()
                except NoAlertPresentException:
                    break

        # Load the page
        try:
            self.browser.get(url)

            # Exit away from any alerts
            dismiss_alerts()

            return self.browser.page_source
        except TimeoutException:
            print("Crawler: ERROR: Could not load", url)
            return self.browser.page_source
        except Exception as e:
            print("Crawler: SERIOUS ERROR: ", e)
            return None

    def _close_browser(self):
        self.browser.quit()
        self.browser = None

    def _start_browser(self):
        assert self.browser is None, \
            "Browser must not exist in order to call start_browser!"

        # Open up browser window
        options = ChromeOptions()
        options.add_argument("--disable-notifications")
        self.browser = Driver(executable_path=self.driver_path,
                              options=options)
        self.browser.set_page_load_timeout(10)


if __name__ == "__main__":
    # Run the crawler
    print("Starting Crawler...")
    crawler = InseCamCrawler(driver_path="./chromedriver.exe",
                             websites_txt="./Websites.txt")
    for ip in crawler:
        print("got IP: ", ip)
