#include "calibration/CorrespondenceMatcher.h"

CorrespondenceMatcher::CorrespondenceMatcher(std::vector<cv::Point2f> pixelCoordinates, cv::Point2f principalAxisX, cv::Point2f principalAxisY, double gridDistance, double distanceThreshold, cv::Mat& image) {
	this->pixelCoordinates = pixelCoordinates;
	this->principalAxisX = principalAxisX;
	this->principalAxisY = principalAxisY;
	this->gridDistance = gridDistance;
	this->distanceThreshold = distanceThreshold;
	this->testImage = image.clone();
}

std::pair<std::vector<cv::Point2f>, std::vector<cv::Point2f>> CorrespondenceMatcher::getPixelGridCorrespondences() {

	std::vector<cv::Point2f> pixelsSorted = PointUtils::sortByDistance(cv::Point2f(0, 0), this->pixelCoordinates);

	while (pixelsSorted.size() > 0 && this->pointCorrespondences.first.size() < pixelsSorted.size()) {
		auto tempPointCorrespondences = std::pair<std::vector<cv::Point2f>, std::vector<cv::Point2f>>();

		this->startRecursion(pixelsSorted, tempPointCorrespondences);

		if (tempPointCorrespondences.first.size() > this->pointCorrespondences.first.size())
			this->pointCorrespondences = tempPointCorrespondences;
	}

	return this->pointCorrespondences;
}

void CorrespondenceMatcher::startRecursion(std::vector<cv::Point2f>& pixelCoords, std::pair<std::vector<cv::Point2f>, std::vector<cv::Point2f>>& connectedPoints) {
	if (pixelCoords.size() == 0)
		return;

	cv::Point2f gridStartPoint = cv::Point2f(0.0, 0.0);
	cv::Point2f pixelStartPoint = pixelCoords.at(0);
	connectedPoints.first.push_back(gridStartPoint);
	connectedPoints.second.push_back(pixelStartPoint);
	pixelCoords.erase(pixelCoords.begin());

	this->checkPoint(gridStartPoint + this->down, pixelStartPoint + this->principalAxisY, pixelCoords, connectedPoints, INVOKE_DIRECTION::DOWN);
	this->checkPoint(gridStartPoint + this->right, pixelStartPoint + this->principalAxisX, pixelCoords, connectedPoints, INVOKE_DIRECTION::RIGHT);
	this->checkPoint(gridStartPoint + this->left, pixelStartPoint - this->principalAxisX, pixelCoords, connectedPoints, INVOKE_DIRECTION::LEFT);
	this->checkPoint(gridStartPoint + this->up, pixelStartPoint - this->principalAxisY, pixelCoords, connectedPoints, INVOKE_DIRECTION::UP);
}

void CorrespondenceMatcher::checkPoint(cv::Point2f gridPos, cv::Point2f pixelPoint, std::vector<cv::Point2f>& pixelCoords, std::pair<std::vector<cv::Point2f>, std::vector<cv::Point2f>>& connectedPoints, int invokeDirection) {
	if (pixelCoords.size() == 0)
		return;

	bool stopped = false;
	for (int i = 0; i < pixelCoords.size(); i++) {
		if (std::abs(cv::norm(pixelPoint - pixelCoords[i])) < this->distanceThreshold) {
			connectedPoints.first.push_back(gridPos);
			connectedPoints.second.push_back(pixelCoords[i]);
			pixelPoint = pixelCoords[i];
			pixelCoords.erase(pixelCoords.begin() + i);

			stopped = true;
			break;
		}
	}

	if (!stopped)
		return;

	this->checkPoint(gridPos + this->down, pixelPoint + this->principalAxisY, pixelCoords, connectedPoints, INVOKE_DIRECTION::DOWN);
	this->checkPoint(gridPos + this->right, pixelPoint + this->principalAxisX, pixelCoords, connectedPoints, INVOKE_DIRECTION::RIGHT);
	this->checkPoint(gridPos + this->left, pixelPoint - this->principalAxisX, pixelCoords, connectedPoints, INVOKE_DIRECTION::LEFT);
	this->checkPoint(gridPos + this->up, pixelPoint - this->principalAxisY, pixelCoords, connectedPoints, INVOKE_DIRECTION::UP);

}