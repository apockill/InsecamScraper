## About
This project scrapes IP addresses from https://www.insecam.org, loads those IP cameras, and then runs each frame through a machine learning model to search for interesting things (such as people). It will then save the frames into a local directory, for later use.

The purpose of the project is to generate large datasets of "in the wild" footage for labeling, which are quite useful for making highly generalized models.

## Requirements
This project requires [EasyInference](https://github.com/apockill/EasyInference) to be installed.