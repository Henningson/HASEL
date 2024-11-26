#pragma once

#include <cmath>
#include <iostream>
#include <fstream>

#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/calib3d.hpp>

#include <Eigen/Dense>
#include <opencv2/core/eigen.hpp>

#include "Calibration.h"
#include "calibration/CorrespondenceMatcher.h"
#include "utils/Correspondences.h"
#include "utils/CurveFitting.h"
#include "utils/PointUtils.h"
#include "utils/Camera.h"


class CameraCalibration : public Calibration {
public:
	CameraCalibration(std::vector<cv::Mat> images, std::vector<std::filesystem::path> filenames, double gridDistance);
	void calibrate();

	Camera getCamera();
	std::vector<cv::Mat> getRotationVectors();
	std::vector<cv::Mat> getTranslationVectors();


protected:
	Camera camera;

	std::vector<cv::Mat> rvecs;
	std::vector<cv::Mat> tvecs;

	
	cv::Mat preprocessImage(cv::Mat& image);
	cv::Mat generateMask(cv::Mat& image, cv::Mat& stats);
	std::vector<cv::Vec4i> getLines(cv::Mat& image);
	std::pair<cv::Mat, cv::Mat> getStats(cv::Mat& image);
};