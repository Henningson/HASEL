#pragma once

#include <cmath>
#include <fstream>

#include "Calibration.h"
#include "calibration/CorrespondenceMatcher.h"
#include "calibration/LaserOptimization.h"

#include "utils/Camera.h"
#include "utils/Correspondences.h"
#include "utils/CurveFitting.h"
#include "utils/ImageUtils.h"
#include "utils/PointUtils.h"
#include "utils/Laser.h"


class LaserCalibration : public Calibration {
public:
	int gridSize;
	LaserCalibration(std::vector<cv::Mat> images, std::vector<std::filesystem::path> filenames, double gridDistance, Laser laser, Camera camera);
	void calibrate();


	Laser getLaser();
	Correspondences getLaserCorrespondences();
	Correspondences getCheckerboardCorrespondences();
	std::vector<cv::Mat> getCheckerboardHomographies();
	void estimateLaserPosition();

	std::pair<std::vector<cv::Vec3f>, std::vector<cv::Vec2f>> fitGrid(std::pair<std::vector<cv::Vec3f>, std::vector<cv::Vec2f>> origin, std::pair<std::vector<cv::Vec3f>, std::vector<cv::Vec2f>> toFit);


protected:
	Camera camera;
	Laser laser;


	Correspondences laserCorrespondences;
	Correspondences checkerboardCorrespondences;
	std::vector<cv::Mat> checkerboardHomographies;

	cv::Mat preprocessImage(cv::Mat& image);
	cv::Mat generateMask(cv::Mat& image, cv::Mat& stats);
	
	std::vector<cv::Vec4i> getLines(cv::Mat& image);
	std::pair<cv::Mat, cv::Mat> getStats(cv::Mat& image);
	std::vector<cv::Point2f> getCorners(const cv::Mat& image, const cv::Mat& mask, int minDistance, int maxCorners);
	void validateCorners(std::vector<cv::Point2f>& corners, const cv::Mat& image, double medianDistance);
	void removeCornersAtPerimeter(std::vector<cv::Point2f>& corners, const cv::Mat& checkerboardROI, double minDistanceAllowed);
	
	std::pair<std::vector<cv::Vec3f>, std::vector<cv::Vec2f>> getPixelGridCorrespondences(std::vector<cv::Point2f> pixelCoordinates, double distanceThreshold, cv::Mat& image, bool isLaser);

	cv::Mat extractLaserROI(const cv::Mat& image);
	cv::Mat extractCheckerboardROI(const cv::Mat& image);

	std::vector<cv::Mat> triangulate(const std::vector<cv::Mat>& homographies, Correspondences& laserCorrespondences, const std::vector<cv::Mat>& translationVecs, const std::vector<cv::Mat>& rotationVecs);

	cv::Mat getLaserOrigin(Correspondences& laserCorrespondences, std::vector<cv::Mat>& laser3DCoordinates);
	cv::Mat getLaserRotation(cv::Mat laserOrigin);

	std::vector<bool> useImage;

};