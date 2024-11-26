#pragma once
#define GLOG_NO_ABBREVIATED_SEVERITIES

#include <vector>

#include <opencv2/core.hpp>
#include <ceres/ceres.h>
#include <ceres/rotation.h>
#include "utils/Laser.h"


struct Vec2VecError {
	Vec2VecError(Eigen::Vector3d point3D, int rayX, int rayY, int vecFieldWidth, int vecFieldHeight) : point3D_(point3D), rayX_(rayX), rayY_(rayY), vecFieldWidth_(vecFieldWidth), vecFieldHeight_(vecFieldHeight) {}

	template <typename T> bool operator()(const T* const transRotAlpha, T* crossError) const {
		//Generate perfect laser-ray
		//transRotAlpha: 0-2 Translation, 3-5 Rotation, 6 Alpha
		typedef Eigen::Matrix<T, 1, 1> Scalar;
		typedef Eigen::Matrix<T, 3, 1> Vec3;
		typedef Eigen:: Matrix<T, 3, 3> Mat3;

		Vec3 ray = Vec3(tan((rayX_ - (vecFieldWidth_ / 2.0)) * transRotAlpha[6]), 
			tan((rayY_ - (vecFieldHeight_ / 2.0)) * transRotAlpha[6]), 
			T(1.0));

		//Move 3D-Point into origin
		Vec3 translatedPoint = Vec3(point3D_[0] - transRotAlpha[0], 
			point3D_[1] - transRotAlpha[1], 
			point3D_[2] - transRotAlpha[2]);

		//Generate rotation Matrix for Laserray
		Vec3 rotVec = Vec3(transRotAlpha[3], transRotAlpha[4], transRotAlpha[5]);
		Vec3 rotatedRay;
		ceres::AngleAxisRotatePoint(rotVec.data(), ray.data(), rotatedRay.data());

		//Rotate laserRay in direction of 3DPoint
		
		//The distance of the crossProduct of the 3D Point and the Laser should be close to zero, if they are parallel
		crossError[0] = point3D_.cross(rotatedRay).norm();
		return true;
	}

private:
	const Eigen::Vector3d point3D_;
	const int rayX_;
	const int rayY_;
	const int vecFieldWidth_;
	const int vecFieldHeight_;
};

class LaserOptimizer {

public:
	LaserOptimizer(Laser& laserField, const std::vector<cv::Mat>& laserPoints3D, const std::vector<std::vector<cv::Vec3f>>& gridPositions);
	Laser optimize(cv::Vec3f startTranslation = cv::Vec3f(0, 0, 0), cv::Vec3f startRotation = cv::Vec3f(0, 0, 0), double startAlpha = 0.0);

	double getAlpha();
	cv::Vec3f getTranslation();
	cv::Vec3f getRotation();

protected:

	double alphaOpt;
	cv::Vec3f translationOpt;
	cv::Vec3f rotationOpt;

	std::vector<std::vector<cv::Vec3f>> gridPositions;
	Laser vectorField;
	std::vector<cv::Mat> laserPoints3D;
	int nrObservations = 0;
};