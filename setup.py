from setuptools import setup


scripts = []

setup(
    name='ip_cam_scraper',
    scripts=scripts,
    version='0.1',
    description='This is a fun side-project for scraping useful data from IP cameras, for use in labeling and training ML models',
    packages=['ipscraper'],
    install_requires=["requests",
                      "selenium",
                      "beautifulsoup4",
                      "dhash",
                      "pillow"],
    zip_safe=False
)