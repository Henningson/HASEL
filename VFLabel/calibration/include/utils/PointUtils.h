#pragma once
#include <vector>
#include <cmath>
#include <iostream>

#include <opencv2/core.hpp>

namespace PointUtils {

	double getMedianOfNeighbourhoods(std::vector<cv::Point2f> points);

	std::vector<cv::Point2f> getNearestNeighbours(cv::Point2f origin, std::vector<cv::Point2f> points, int numOfNeighbours);

	std::vector<cv::Point2f> sortByDistance(cv::Point2f compare, std::vector<cv::Point2f> points);

	cv::Mat skewSymmetricMatrix(cv::Mat vec);

	std::pair<std::vector<cv::Point2f>, std::vector<double>> normalizedHoughTransform(const cv::Mat& image, const std::vector<cv::Point2f>& cornerPoints, bool filter = true);

	std::vector<cv::Vec3f> matToVec3(cv::Mat mat);

	std::vector<cv::Vec2f> matToVec2(cv::Mat mat);

	cv::Mat vec3ToMat(std::vector<cv::Vec3f> vec);
	cv::Mat vec2ToMat(std::vector<cv::Vec2f> vec);
}