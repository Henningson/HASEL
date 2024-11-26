#pragma once

#include <opencv2/core.hpp>

//A class handling pixel, grid and 3d-location correspondences
class Correspondences {
public:
	Correspondences();
	Correspondences(std::vector<std::vector<cv::Point2f>> gridCoords, std::vector<std::vector<cv::Point2f>> pixelCoords);
	Correspondences(std::vector<std::vector<cv::Vec3f>> gridCoords, std::vector<std::vector<cv::Point2f>> pixelCoords);
	Correspondences(std::vector<std::vector<cv::Vec3f>> gridCoords, std::vector<std::vector<cv::Vec2f>> pixelCoords);
	Correspondences(std::vector<std::vector<cv::Vec3f>> gridCoords, std::vector<std::vector<cv::Vec2f>> pixelCoords, std::vector<std::vector<cv::Vec3f>> worldCoords);
	
	void addGridPixelCorrespondences(std::vector<cv::Vec3f> gridLocation, std::vector<cv::Vec2f> pixelLocation);
	void addGridPixelCorrespondences(std::vector<cv::Point2f> gridLocation, std::vector<cv::Point2f> pixelLocation);

	void addWorldCoords(std::vector<cv::Vec3f> worldCoords);
	void setWorldCoords(std::vector<std::vector<cv::Vec3f>> worldCoords);

	std::vector<cv::Mat> getBundledWorldCoordinates();

	std::vector<std::vector<cv::Vec3f>>& getGrid();
	std::vector<std::vector<cv::Vec2f>>& getPixels();
	std::vector<cv::Vec3f>& getGridAt(int i);
	std::vector<cv::Vec2f>& getPixelsAt(int i);
	cv::Vec3f getGridPoint(int i, int j);
	cv::Vec2f getPixelPoint(int i, int j);

protected:
	std::vector<std::vector<cv::Vec3f>> gridPoints;
	std::vector<std::vector<cv::Vec2f>> pixelPoints;
	std::vector<std::vector<cv::Vec3f>> worldCoordinates;

	std::vector<cv::Vec3f> transformToVec3(std::vector<cv::Point2f> points, float zValue = 0.0);
	std::vector<std::vector<cv::Vec3f>> transformToVec3(std::vector<std::vector<cv::Point2f>> points, float zValue = 0.0);
	std::vector<cv::Vec2f> transformToVec2(std::vector<cv::Point2f> points);
	std::vector<std::vector<cv::Vec2f>> transformToVec2(std::vector<std::vector<cv::Point2f>> points);
};