#pragma once

#include <string>
#include <opencv2/core.hpp>
#include <opencv2/calib3d.hpp>

class Camera {
public:
	Camera();
	Camera(std::string path);
	Camera(cv::Mat cameraMatrix, cv::Mat distortionCoefficients, cv::Size size);


	void loadFromFile(std::string path);
	void saveToFile(std::string path);

	cv::Mat getCameraMatrix();
	cv::Mat getDistortionCoefficients();
	int getImageWidth();
	int getImageHeight();
	cv::Size getImageSize();

	cv::Mat undistortImage(cv::Mat image);
	cv::Mat undistortPoints(cv::Mat image);

protected:
	cv::Mat cameraMatrix;
	cv::Mat distortionCoefficients;
	int width;
	int height;
	cv::Size size;
};