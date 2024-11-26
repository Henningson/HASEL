#include "utils/Correspondences.h"

Correspondences::Correspondences() {
	this->gridPoints = std::vector<std::vector<cv::Vec3f>>();
	this->pixelPoints = std::vector<std::vector<cv::Vec2f>>();
	this->worldCoordinates = std::vector<std::vector<cv::Vec3f>>();
}

Correspondences::Correspondences(std::vector<std::vector<cv::Vec3f>> gridCoords, std::vector<std::vector<cv::Point2f>> pixelCoords) {
	this->gridPoints = gridCoords;
	this->pixelPoints = this->transformToVec2(pixelCoords);
	this->worldCoordinates = std::vector<std::vector<cv::Vec3f>>();
}

Correspondences::Correspondences(std::vector<std::vector<cv::Point2f>> gridCoords, std::vector<std::vector<cv::Point2f>> pixelCoords) {
	this->gridPoints = this->transformToVec3(gridCoords);
	this->pixelPoints = this->transformToVec2(pixelCoords);
	this->worldCoordinates = std::vector<std::vector<cv::Vec3f>>();
}

Correspondences::Correspondences(std::vector<std::vector<cv::Vec3f>> gridCoords, std::vector<std::vector<cv::Vec2f>> pixelCoords, std::vector<std::vector<cv::Vec3f>> worldCoords) {
	this->gridPoints = gridCoords;
	this->pixelPoints = pixelCoords;
	this->worldCoordinates = worldCoords;
}

void Correspondences::addGridPixelCorrespondences(std::vector<cv::Vec3f> gridLocation, std::vector<cv::Vec2f> pixelLocation) {
	this->gridPoints.push_back(gridLocation);
	this->pixelPoints.push_back(pixelLocation);
}

void Correspondences::addGridPixelCorrespondences(std::vector<cv::Point2f> gridLocation, std::vector<cv::Point2f> pixelLocation) {
	this->gridPoints.push_back(this->transformToVec3(gridLocation));
	this->pixelPoints.push_back(this->transformToVec2(pixelLocation));
}


void Correspondences::addWorldCoords(std::vector<cv::Vec3f> worldCoords) {
	this->worldCoordinates.push_back(worldCoords);
}

void Correspondences::setWorldCoords(std::vector<std::vector<cv::Vec3f>> worldCoords) {
	this->worldCoordinates = worldCoords;
}

std::vector<cv::Mat> Correspondences::getBundledWorldCoordinates() {
	return std::vector<cv::Mat>();
}

std::vector<std::vector<cv::Vec3f>>& Correspondences::getGrid() {
	return this->gridPoints;
}

std::vector<std::vector<cv::Vec2f>>& Correspondences::getPixels() {
	return this->pixelPoints;
}

std::vector<cv::Vec3f>& Correspondences::getGridAt(int i) {
	return this->gridPoints.at(i);
}

std::vector<cv::Vec2f>& Correspondences::getPixelsAt(int i) {
	return this->pixelPoints.at(i);
}

cv::Vec3f Correspondences::getGridPoint(int i, int j) {
	return this->gridPoints.at(i).at(j);
}

cv::Vec2f Correspondences::getPixelPoint(int i, int j) {
	return this->pixelPoints.at(i).at(j);
}

std::vector<cv::Vec3f> Correspondences::transformToVec3(std::vector<cv::Point2f> points, float zValue) {
	std::vector<cv::Vec3f> transPoints = std::vector<cv::Vec3f>();
	for (int i = 0; i < points.size(); i++)
		transPoints.push_back(cv::Vec3f(points.at(i).x, points.at(i).y, zValue));
	return transPoints;
}

std::vector<cv::Vec2f> Correspondences::transformToVec2(std::vector<cv::Point2f> points) {
	std::vector<cv::Vec2f> transPoints = std::vector<cv::Vec2f>();
	for (int i = 0; i < points.size(); i++)
		transPoints.push_back(cv::Vec2f(points.at(i).x, points.at(i).y));
	return transPoints;
}

std::vector<std::vector<cv::Vec2f>> Correspondences::transformToVec2(std::vector<std::vector<cv::Point2f>> points) {
	return std::vector<std::vector<cv::Vec2f>>();
}

std::vector<std::vector<cv::Vec3f>> Correspondences::transformToVec3(std::vector<std::vector<cv::Point2f>> points, float zValue) {
	return std::vector<std::vector<cv::Vec3f>>();
}