from argparse import ArgumentParser

from ipscraper.extraction import Extractor
from ipscraper.crawler import InseCamCrawler

from easy_inference.models import ObjectDetector

description = ("Scrape insecure camera IP's, load them, read frames, run those "
               "frames through a ML model, and save the interesting frames. ")

if __name__ == "__main__":
    parser = ArgumentParser(description=description)
    parser.add_argument("--model-path", required=True, type=str,
                        help="Path to the machine learning model for detection")
    parser.add_argument("--model-labels", required=True, type=str,
                        help="Labels for the ML model")
    parser.add_argument("--save-dir", required=True, type=str,
                        help="Directory to save frames to")
    parser.add_argument("--num_workers", type=str, default=750,
                        help="Number of open cameras at any given time")
    parser.add_argument("--class-names", type=list, default=["person"],
                        help="Type of object to search for")
    parser.add_argument("--url-seeds-file", required=True, type=str,
                        help="A text file that contains, line by line, "
                             " URL seeds for pages from "
                             "https://www.insecam.org which will be used to get"
                             " IP camera addresses")
    parser.add_argument("--chromedriver-path", required=True, type=str,
                        help="Path to chromedriver.exe, required for scraping")
    args = parser.parse_args()

    detector = ObjectDetector.from_path(args.model_path, args.model_labels)
    scraper = InseCamCrawler(args.chromedriver_path, args.url_seeds_file)
    extractor = Extractor(ip_addresses=scraper,
                          class_names=args.class_names,
                          detector=detector,
                          output_dir=args.save_dir,
                          workers=args.num_workers)
    while True:
        extractor.extract()
