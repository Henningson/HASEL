#pragma once

#include <iostream>

#include <opencv2/core.hpp>
#include <opencv2/calib3d.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/highgui.hpp>


class RecursionGrid {
protected:
	cv::Mat homography;
	cv::Mat grid;
	cv::Mat visited;

	double gridDistance;
	double distanceThreshold;
	int gridMidPoint;
	int gridSize;
	
	std::vector<cv::Point2f> pixelCoordinates;
	std::pair<std::vector<cv::Point2f>, std::vector<cv::Point2f>> pointCorrespondences;

	int minX = 0;
	int minY = 0;


	cv::Point2f up, down, right, left;
	enum INVOKE_DIRECTION { UP, RIGHT, DOWN, LEFT };

	int iSave = 0;

public:
	RecursionGrid(cv::Mat homography, std::vector<cv::Point2f> pixelCoordinates, std::pair<std::vector<cv::Point2f>, std::vector<cv::Point2f>> pointCorrespondences, double gridDistance, double distanceThreshold);
	std::pair<std::vector<cv::Point2f>, std::vector<cv::Point2f>> buildGrid();
	cv::Mat testImage;

protected:
	cv::Point2i transformToHomogenous(cv::Point2f point);
	void startRecursion(cv::Point2f gridPos);
	void checkPoint(cv::Point2f gridPos, int invokeDirection);

};