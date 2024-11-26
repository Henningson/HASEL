#pragma once

#include <Eigen/Dense>
#include <opencv2/core.hpp>

double polyeval(Eigen::VectorXd coeffs, double x);

Eigen::VectorXd polyfit(Eigen::VectorXd xvals, Eigen::VectorXd yvals, int order);

double getY(cv::Vec4f line_points, double x);

std::pair<cv::Mat, cv::Mat> fitRay(cv::Mat laserPoints);