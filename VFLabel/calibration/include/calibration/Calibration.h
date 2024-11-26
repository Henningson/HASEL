#pragma once

#include <string>
#include <filesystem>
#include <iostream>

#include <opencv2/core.hpp>
#include <opencv2/calib3d.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>

#include "utils/ImageUtils.h"

class Calibration {
protected:
	std::vector<cv::Mat> images;
	std::vector<std::filesystem::path> filenames;
	double gridDistance;
	bool debugMode = false;

	double qualityLevel = 0.01;
	int gradientSize = 7;
	bool useHarrisDetector = false; 
	double harrisKValue = 0.04;

protected:
	virtual cv::Mat preprocessImage(cv::Mat& image) = 0;
	virtual std::pair<cv::Mat, cv::Mat> getStats(cv::Mat& image) = 0;
	virtual cv::Mat generateMask(cv::Mat& image, cv::Mat& stats) = 0;
	virtual std::vector<cv::Vec4i> getLines(cv::Mat& image) = 0;

public:
	Calibration(std::vector<cv::Mat> &images, std::vector<std::filesystem::path> &filenames, double gridDistance);
	virtual void calibrate() = 0;

	void setGridDistance(double gridDistance);
	void setHarrisKValue(double kValue);
	void toggleHarrisDetector();
	void setGradientSize(int val);
	void setQualityLevel(double qualityLevel);
	void setDebugMode(bool val);
};