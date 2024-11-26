#include "calibration/CameraCalibration.h"

CameraCalibration::CameraCalibration(std::vector<cv::Mat> images, std::vector<std::filesystem::path> filenames, double gridDistance)
	: Calibration{ images, filenames, gridDistance } {}



Camera CameraCalibration::getCamera() {
	return this->camera;
}

std::vector<cv::Mat> CameraCalibration::getRotationVectors() {
	return this->rvecs;
}

std::vector<cv::Mat> CameraCalibration::getTranslationVectors() {
	return this->tvecs;
}

void CameraCalibration::calibrate() {
	Correspondences corres = Correspondences();

	for (cv::Mat image : images) {
		cv::Mat grayImage, copy;
		image.copyTo(copy);
		cv::cvtColor(image, grayImage, cv::COLOR_BGR2GRAY);

		cv::Mat bwimage = this->preprocessImage(grayImage);
		auto stats = this->getStats(bwimage);
		cv::Mat maskImage = this->generateMask(grayImage, stats.first);
		std::vector<cv::Point2f> corners;
		double minDistance = stats.first.at<int>(stats.first.rows / 2, 2);
		int blockSize = stats.first.at<int>(stats.first.rows / 2, 2);

		cv::goodFeaturesToTrack(grayImage, corners, MAX(stats.first.rows, 1), this->qualityLevel, minDistance, maskImage / 255, blockSize, this->gradientSize, this->useHarrisDetector, this->harrisKValue);
		cv::cornerSubPix(grayImage, corners, cv::Size(5, 5), cv::Size(-1, -1), cv::TermCriteria(cv::TermCriteria::EPS + cv::TermCriteria::COUNT, 40, 0.001));

		auto unitVectorAndLengthCB = PointUtils::normalizedHoughTransform(image, corners, false);

		cv::Point2f principalAxis1 = unitVectorAndLengthCB.first[0] * unitVectorAndLengthCB.second[0];
		cv::Point2f principalAxis2 = unitVectorAndLengthCB.first[1] * unitVectorAndLengthCB.second[1];
		principalAxis1.y = -principalAxis1.y;
		principalAxis2.x = -principalAxis2.x;

		CorrespondenceMatcher corresMatch = CorrespondenceMatcher(corners, principalAxis1, principalAxis2, 2.0, 10.0, image);

		auto pixelGridCorrespondences = corresMatch.getPixelGridCorrespondences();

		for (int i = 0; i < pixelGridCorrespondences.second.size(); i++) {
			cv::circle(copy, pixelGridCorrespondences.second.at(i), 3, cv::Scalar(0, 255, 0), -1);
			cv::putText(copy, "(" + std::to_string((int)pixelGridCorrespondences.first.at(i).x) + ", " + std::to_string((int)pixelGridCorrespondences.first.at(i).y) + ")", pixelGridCorrespondences.second.at(i), 1, 0.8, cv::Scalar(255, 255, 255));
		}

		cv::line(copy, pixelGridCorrespondences.second.at(0), pixelGridCorrespondences.second.at(0) + principalAxis1, cv::Scalar(0, 255, 0), 2);
		cv::line(copy, pixelGridCorrespondences.second.at(0), pixelGridCorrespondences.second.at(0) + principalAxis2, cv::Scalar(0, 0, 255), 2);


		cv::imshow("Copy", copy);
		cv::waitKey(1);

		if (pixelGridCorrespondences.first.size() == 0 || pixelGridCorrespondences.second.size() == 0 || pixelGridCorrespondences.first.size() != pixelGridCorrespondences.second.size())
			continue;
		
		corres.addGridPixelCorrespondences(pixelGridCorrespondences.first, pixelGridCorrespondences.second);
	}

	cv::Mat stddevIntrinsic;
	cv::Mat stddevExtrinsic;
	cv::Mat newPoints;
	cv::Mat perViewError;

	std::cout << "Finished calibration" << std::endl;

	cv::Mat cameraMatrix, distCoeffs;
	auto reprojError = cv::calibrateCameraRO(corres.getGrid(), corres.getPixels(), cv::Size(images[0].cols, images[0].rows), 0, cameraMatrix, distCoeffs, this->rvecs, this->tvecs, newPoints, 
		cv::CALIB_USE_LU | cv::CALIB_FIX_K6 | cv::CALIB_FIX_K5 | cv::CALIB_FIX_K4 | cv::CALIB_FIX_K3);

	std::cout << "ReprojError=" << reprojError << std::endl;
	std::cout << "Camera Mat=" << cameraMatrix << std::endl;
	std::cout << "Dist Coeffs=" << distCoeffs << std::endl;

	this->camera = Camera(cameraMatrix, distCoeffs, images[0].size());
}

std::vector<cv::Vec4i> CameraCalibration::getLines(cv::Mat& image) {
	cv::Mat src, dst, cdstP;
	src = image.clone();
	cv::Canny(src, dst, 50, 200, 3);

	cv::cvtColor(dst, cdstP, cv::COLOR_GRAY2BGR);

	// Probabilistic Line Transform
	std::vector<cv::Vec4i> linesP;
	cv::HoughLinesP(dst, linesP, 1, CV_PI / 180, 20, 650, 100);

	return linesP;
}

cv::Mat CameraCalibration::preprocessImage(cv::Mat& image) {
	cv::Mat disk_element = cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(17, 17));
	IMUtils::imadjust(image, image, 0.0, 1.0, 0.0, 1.0);

	cv::morphologyEx(image, image, cv::MORPH_TOPHAT, disk_element);

	cv::Mat bwimage = cv::Mat(image.size(), image.type());
	cv::threshold(image, bwimage, 0, 255, cv::THRESH_BINARY | cv::THRESH_OTSU);
	return bwimage;
}


cv::Mat CameraCalibration::generateMask(cv::Mat &image, cv::Mat& filteredStats) {
	cv::Mat maskImage = cv::Mat::zeros(image.rows, image.cols, image.type());

	for (int i = 0; i < filteredStats.rows; i++)
		cv::rectangle(maskImage, cv::Rect(filteredStats.at<int>(i, 0), filteredStats.at<int>(i, 1), filteredStats.at<int>(filteredStats.rows / 2, 2), filteredStats.at<int>(filteredStats.rows / 2, 3)), 255, -1);

	return maskImage;
}

std::pair<cv::Mat, cv::Mat> CameraCalibration::getStats(cv::Mat& image) {
	cv::Mat labelImage;
	cv::Mat stats;
	cv::Mat centroids;

	int numLabels = cv::connectedComponentsWithStats(image, labelImage, stats, centroids);

	cv::Mat idx;
	cv::sortIdx(stats.col(4), idx, cv::SORT_EVERY_COLUMN + cv::SORT_ASCENDING);
	cv::Mat sorted_stats = cv::Mat(0, 5, stats.type());
	cv::Mat sorted_centroids = cv::Mat(0, 2, centroids.type());
	int median = stats.at<int>(idx.at<int>(stats.rows / 2), 4);

	for (int i = 0; i < stats.rows; i++) {
		if (stats.at<int>(idx.at<int>(i), 4) < int(median * 0.05) || stats.at<int>(idx.at<int>(i), 4) > int(median * 1.95))
			continue;

		sorted_stats.push_back(stats.row(idx.at<int>(i)));
		sorted_centroids.push_back(centroids.row(idx.at<int>(i)));
	}

	cv::Mat ascending = cv::Mat(sorted_stats.rows, 1, sorted_stats.type());
	for (int i = 0; i < sorted_stats.rows; i++) {
		ascending.at<int>(i) = i;
	}

	cv::Mat in;
	cv::Vec4f line;
	cv::hconcat(ascending, sorted_stats.col(4), in);
	cv::fitLine(in, line, cv::DIST_L2, 0, 0.01, 0.01);

	cv::Vec2f starting_point = cv::Vec2f(line[2], line[3]);
	cv::Vec2f end_point = starting_point + (cv::Vec2f(line[0], line[1]) * (sorted_stats.rows - 1));

	int lower_index = 0;
	double lower_y = getY(line, 0.0);

	int upper_index = 0;
	double upper_y = getY(line, double(sorted_stats.rows) - 1.0);

	for (int i = 0; i < sorted_stats.rows; i++) {
		if (sorted_stats.at<int>(i, 4) > lower_y) {
			lower_index = i;
			break;
		}
	}

	for (int i = sorted_stats.rows - 1; i > 0; i--) {
		if (sorted_stats.at<int>(sorted_stats.rows - 1 - i, 4) < upper_y) {
			upper_index = i;
			break;
		}
	}

	return std::make_pair(sorted_stats(cv::Range(lower_index, upper_index), cv::Range(0, sorted_stats.cols)), sorted_centroids(cv::Range(lower_index, upper_index), cv::Range(0, sorted_centroids.cols)));
}