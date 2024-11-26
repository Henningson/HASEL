#pragma once

#include <string>
#include <cmath>

#include <opencv2/core.hpp>
#include <opencv2/calib3d.hpp>

class Laser {
public:
	Laser();
	Laser(std::string path);
	Laser(int width, double alpha, cv::Mat offsets = cv::Mat(), cv::Vec3f rotation = cv::Vec3f(0, 0, 0), cv::Vec3f translation = cv::Vec3f(0, 0, 0));
	Laser(int width, int height, double alpha, cv::Mat offsets = cv::Mat(), cv::Vec3f rotation = cv::Vec3f(0, 0, 0), cv::Vec3f translation = cv::Vec3f(0, 0, 0));

	void loadFromFile(std::string path);
	void saveToFile(std::string path);

	cv::Vec3f getVec(int x, int y);
	cv::Mat getField();

	int getWidth();
	int getHeight();
	cv::Vec3f getRotation();
	cv::Mat getRotationMat();
	cv::Vec3f getTranslation();

protected:
	int width = 0;
	int height = 0;
	void buildVectorField(int width, int height, double alpha);
	cv::Mat vectorField;
	cv::Mat offsets;
	cv::Vec3f rotationVec;
	cv::Vec3f translationVec;
};