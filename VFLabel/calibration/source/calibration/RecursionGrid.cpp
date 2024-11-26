#include "calibration/RecursionGrid.h"

RecursionGrid::RecursionGrid(cv::Mat homography, std::vector<cv::Point2f> pixelCoordinates, std::pair<std::vector<cv::Point2f>, std::vector<cv::Point2f>> pointCorrespondences, double gridDistance, double distanceThreshold) {
	this->homography = homography;
	this->pixelCoordinates = std::vector<cv::Point2f>(pixelCoordinates.begin(), pixelCoordinates.end());
	this->pointCorrespondences = pointCorrespondences;
	this->gridDistance = gridDistance;
	this->distanceThreshold = distanceThreshold;

	int numberOfPoints = pixelCoordinates.size();
	this->gridSize = std::ceil(std::sqrt(double(numberOfPoints)));
	this->gridSize = gridSize * 2 + 1;
	this->gridMidPoint = std::floor(gridSize * 0.5);

	this->up = cv::Point2f(0.0, -this->gridDistance);
	this->down = cv::Point2f(0.0, this->gridDistance);
	this->right = cv::Point2f(this->gridDistance, 0.0);
	this->left = cv::Point2f(-this->gridDistance, 0.0);

	this->visited = cv::Mat::zeros(gridSize, gridSize, CV_8UC1);

	for (int i = -1; i < 2; i++) {
		for (int j = -1; j < 2; j++) {
			this->visited.at<uchar>(this->gridMidPoint + i, this->gridMidPoint + j) = 1;
		}
	}
}

std::pair<std::vector<cv::Point2f>, std::vector<cv::Point2f>> RecursionGrid::buildGrid() {
	this->startRecursion(cv::Point2f(-this->gridDistance, -this->gridDistance));
	this->startRecursion(cv::Point2f(this->gridDistance, -this->gridDistance));
	this->startRecursion(cv::Point2f(-this->gridDistance, -this->gridDistance));
	this->startRecursion(cv::Point2f(-this->gridDistance, this->gridDistance));

	for (cv::Point2f& gridPoint : this->pointCorrespondences.first) {
		gridPoint /= this->gridDistance;
		gridPoint -= cv::Point2f(this->minX, this->minY);
	}

	return this->pointCorrespondences;
}

cv::Point2i RecursionGrid::transformToHomogenous(cv::Point2f point) {
	cv::Point2f homogenousPoint = point / this->gridDistance;
	return cv::Point2i(int(homogenousPoint.x) + this->gridMidPoint, int(homogenousPoint.y) + this->gridMidPoint);
}

void RecursionGrid::startRecursion(cv::Point2f gridPos) {
	this->checkPoint(gridPos + up, INVOKE_DIRECTION::UP);
	this->checkPoint(gridPos + right, INVOKE_DIRECTION::RIGHT);
	this->checkPoint(gridPos + down, INVOKE_DIRECTION::DOWN);
	this->checkPoint(gridPos + left, INVOKE_DIRECTION::LEFT);
}



void RecursionGrid::checkPoint(cv::Point2f gridPos, int invokeDirection) {
	cv::Point2i pointIndices = this->transformToHomogenous(gridPos);
	
	if (pointIndices.x < 0 || pointIndices.y < 0 || pointIndices.x >= this->gridSize || pointIndices.y >= this->gridSize)
		return;

	if (this->visited.at<uchar>(pointIndices.y, pointIndices.x) == 1)
		return;

	this->visited.at<uchar>(pointIndices.y, pointIndices.x) = 1;

	if (this->pixelCoordinates.size() == 0)
		return;

	cv::Mat point = cv::Mat(3, 1, this->homography.type());
	point.at<double>(0, 0) = gridPos.x;
	point.at<double>(1, 0) = gridPos.y;
	point.at<double>(2, 0) = 1.0;
	cv::Mat transformed = this->homography * point;
	transformed = transformed / transformed.at<double>(2, 0);

	bool correspondingPointFound = false;
	for (int i = 0; i < pixelCoordinates.size(); i++) {
		if (cv::norm(cv::Point2f(transformed.at<double>(0, 0), transformed.at<double>(1, 0)) - pixelCoordinates.at(i)) < this->distanceThreshold) {
			int xNorm = int(gridPos.x / this->gridDistance);
			int yNorm = int(gridPos.y / this->gridDistance);
			if (xNorm < this->minX)
				this->minX = xNorm;

			if (yNorm < this->minY)
				this->minY = yNorm;

			this->pointCorrespondences.first.push_back(gridPos);
			this->pointCorrespondences.second.push_back(pixelCoordinates.at(i));
			correspondingPointFound = true;
			pixelCoordinates.erase(pixelCoordinates.begin() + i);
			break;
		}
	}

	if (!correspondingPointFound)
		return;

	this->homography = cv::findHomography(this->pointCorrespondences.first, this->pointCorrespondences.second);

	this->checkPoint(gridPos + left, INVOKE_DIRECTION::LEFT);
	this->checkPoint(gridPos + down, INVOKE_DIRECTION::DOWN);
	this->checkPoint(gridPos + right, INVOKE_DIRECTION::RIGHT);
	this->checkPoint(gridPos + up, INVOKE_DIRECTION::UP);

	return;
}
