import os
import hashlib
from time import sleep
from pathlib import Path
from threading import Thread

import cv2
import dhash
from PIL import Image


class Extractor:
    MAX_SAVE_PER_STREAM = 15
    MAX_BLANK = 10

    def __init__(self, class_names, ip_scraper, detector, output_dir, workers):
        """
        :param class_names: A list of strings of classes to search for
            ["person", "car", "dog"]
        :param ip_scraper: The InseCamScraper object
        :param detector: A detector with a .predict function that returns
            Detection objects
        :param output_dir: Directory to save images to
        :param workers: Maximum number of workers to be downloading images
            at any given time
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        self.class_names = class_names
        self.ip_generator = ip_scraper.__iter__()
        self.scraper = ip_scraper
        self.detector = detector
        self.output_dir = output_dir
        self.num_workers = int(workers)

        # State
        self.active_cameras = []

    def extract(self):
        ip_buffer = []
        while True:
            # Find inactive cameras and record useful IP's
            inactive_cameras = [cam for cam in self.active_cameras
                                if not cam.is_alive()]
            for cam in inactive_cameras:
                if cam.saved_count > 0:
                    self.record_ip(cam.url)

            # Remove inactive cameras
            self.active_cameras = [cam for cam in self.active_cameras
                                   if cam not in inactive_cameras]

            if len(ip_buffer) < self.num_workers:
                next_ip = next(self.ip_generator, None)
                if next_ip is not None:
                    ip_buffer.append(next_ip)
                elif len(ip_buffer) == 0:
                    print("Extractor: Buffer is empty, and no more IP. Ending!")
                    break

            # Create a new worker if there are not enough
            while len(self.active_cameras) < self.num_workers:
                if len(ip_buffer) == 0: break
                worker = ExtractionWorker(url=ip_buffer.pop(0),
                                          class_names=self.class_names,
                                          detector=self.detector,
                                          output_dir=self.output_dir,
                                          max_blank=self.MAX_BLANK,
                                          max_save=self.MAX_SAVE_PER_STREAM)
                self.active_cameras.append(worker)
                print("Extractor: Num Workers:", len(self.active_cameras),
                      "Num Buffered IPs:", len(ip_buffer))

            sleep(.1)

    def record_ip(self, ip):
        with open("./useful_ip_cache.txt", "a+") as f:
            f.seek(0)
            line_found = any(ip in line for line in f)
            if not line_found:
                f.seek(0, os.SEEK_END)
                f.write(ip + "\n")





class ExtractionWorker(Thread):
    DHASH_SIZE = 4

    def __init__(self, url, class_names, detector, output_dir, max_blank,
                 max_save):
        super().__init__()

        # Statistics
        self.blank_count = 0
        self.total_count = 0
        self.saved_count = 0

        # limits
        self.max_blank = max_blank
        self.max_save = max_save

        self.detector = detector
        self.class_names = class_names
        self.output_dir = output_dir
        self.url = url

        self.filename_prefix = hashlib.sha256(self.url.encode('utf-8'))
        self.filename_prefix = self.filename_prefix.hexdigest()[:10]

        # Start the worker thread
        self.start()

    def run(self):
        cap = cv2.VideoCapture(self.url)
        sleep(3)

        self.blank_count = 0
        self.saved_count = 0
        self.total_count = 0

        while self.blank_count < self.max_blank \
                and self.saved_count < self.max_save:
            _, frame = cap.read()
            sleep(1)
            if frame is None:
                print("Workers: Stopped receiving frames. Received: ",
                      self.total_count, "Saved: ", self.saved_count)
                return
            self.total_count += 1

            preds = self.detector.predict([frame])[0]
            if any([pred.name in self.class_names for pred in preds]):
                d_hash = dhash.dhash_int(Image.fromarray(frame),
                                         self.DHASH_SIZE)
                filename = self.filename_prefix + "_" + \
                           str(d_hash) + ".jpg"
                save_path = Path(self.output_dir) / filename
                if save_path.exists():
                    self.blank_count += 1
                    continue

                cv2.imwrite(str(save_path), frame)
                print("Saving!", filename)

                self.saved_count += 1
                self.blank_count = 0
                continue

            self.blank_count += 1
        print("Worker: Reached maximum frames. Received", self.total_count,
              "Saved: ", self.saved_count)
