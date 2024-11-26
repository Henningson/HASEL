#pragma once

#define USE_MATH_DEFINES
#include <cmath>
#include <filesystem>
#include <vector>

#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/highgui.hpp>

namespace IMUtils {

	std::vector<cv::Mat> loadImages(std::vector<std::filesystem::path> paths, int loadOpt = 1);

	double getScreenspaceAngleOfLine(cv::Vec4i line);

	void stretchlimFromHist(const cv::Mat& hist, double* low_value, double* high_value, double low_fract, double high_fract, unsigned int histSum);

	int bitsFromDepth(int depth);

	void stretchlim(const cv::InputArray _image, double* low_value, double* high_value, double low_fract, double high_fract);

	void imadjust(const cv::InputArray _src, cv::OutputArray _dst, double low_in, double high_in, double low_out, double high_out);

	cv::Mat homomorphic(const cv::Mat& image, double gh, double gl, double d0, double c);

	void flipQuadrants(cv::Mat& image);

};