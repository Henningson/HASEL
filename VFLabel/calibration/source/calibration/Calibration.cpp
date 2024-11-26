#include "calibration/Calibration.h"


Calibration::Calibration(std::vector<cv::Mat> &images, std::vector<std::filesystem::path>& filenames, double gridDistance) {
	this->images = images;
	this->filenames = filenames;
	this->gridDistance = gridDistance;
}

void Calibration::setDebugMode(bool val) {
	this->debugMode = val;
}

void Calibration::setGridDistance(double gridDistance) {
	this->gridDistance = gridDistance;
}

void Calibration::setHarrisKValue(double kValue) {
	this->harrisKValue = kValue;
}

void Calibration::toggleHarrisDetector() {
	this->useHarrisDetector = !this->useHarrisDetector;
}

void Calibration::setGradientSize(int val) {
	this->gradientSize = val;
}

void Calibration::setQualityLevel(double qualityLevel) {
	this->qualityLevel = qualityLevel;
}