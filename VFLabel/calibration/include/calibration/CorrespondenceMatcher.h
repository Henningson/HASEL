#pragma once

#include <vector>
#include <iostream>

#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>

#include "utils/PointUtils.h"

class CorrespondenceMatcher {
protected:
	double gridDistance;
	double distanceThreshold;

	std::vector<cv::Point2f> pixelCoordinates;

	std::pair<std::vector<cv::Point2f>, std::vector<cv::Point2f>> pointCorrespondences;

	cv::Point2f principalAxisX;
	cv::Point2f principalAxisY;

	cv::Point2f up = cv::Point2f(0.0, -1.0); 
	cv::Point2f down = cv::Point2f(0.0, 1.0);
	cv::Point2f right = cv::Point2f(1.0, 0.0);
	cv::Point2f left = cv::Point2f(-1.0, 0.0);
	enum INVOKE_DIRECTION { UP, RIGHT, DOWN, LEFT };

	cv::Mat testImage;

public:
	CorrespondenceMatcher(std::vector<cv::Point2f> pixelCoordinates, cv::Point2f principalAxisX, cv::Point2f principalAxisY, double gridDistance, double distanceThreshold, cv::Mat& image);
	std::pair<std::vector<cv::Point2f>, std::vector<cv::Point2f>> getPixelGridCorrespondences();
	
protected:
	void startRecursion(std::vector<cv::Point2f>& pixelCoords, std::pair<std::vector<cv::Point2f>, std::vector<cv::Point2f>>& connectedPoints);
	void checkPoint(cv::Point2f gridPos, cv::Point2f pixelPoint, std::vector<cv::Point2f>& pixelCoords, std::pair<std::vector<cv::Point2f>, std::vector<cv::Point2f>>& connectedPoints, int invokeDirection);

};