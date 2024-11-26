#include "utils/Camera.h"

Camera::Camera() {
	this->cameraMatrix = cv::Mat();
	this->distortionCoefficients = cv::Mat();
	this->size = cv::Size(0, 0);
	this->width = 0;
	this->height = 0;
}

Camera::Camera(std::string path) {
	this->loadFromFile(path);
}

Camera::Camera(cv::Mat cameraMatrix, cv::Mat distortionCoefficients, cv::Size size) {
	this->cameraMatrix = cameraMatrix;
	this->distortionCoefficients = distortionCoefficients;
	this->size = size;
}

void Camera::loadFromFile(std::string path) {
	cv::FileStorage fs(path, cv::FileStorage::READ);
	fs["CameraMatrix"] >> this->cameraMatrix;
	fs["DistortionCoefficients"] >> this->distortionCoefficients;
	fs["size"] >> this->size;
	this->width = this->size.width;
	this->height = this->size.height;
	fs.release();
}

void Camera::saveToFile(std::string path) {
	cv::FileStorage fs(path, cv::FileStorage::WRITE);
	fs << "CameraMatrix" << this->cameraMatrix;
	fs << "DistortionCoefficients" << this->distortionCoefficients;
	fs << "size" << this->size;
	fs.release();
}

cv::Mat Camera::getCameraMatrix() {
	return this->cameraMatrix;
}

cv::Mat Camera::getDistortionCoefficients() {
	return this->distortionCoefficients;
}

int Camera::getImageWidth() {
	return this->size.width;
}

int Camera::getImageHeight() {
	return this->size.width;
}

cv::Size Camera::getImageSize() {
	return this->size;
}

cv::Mat Camera::undistortImage(cv::Mat image) {
	cv::Mat undistorted;
	cv::undistort(image, undistorted, this->cameraMatrix, this->distortionCoefficients);
	return undistorted;
}

cv::Mat Camera::undistortPoints(cv::Mat image) {
	cv::Mat undistorted;
	cv::undistortPoints(image, undistorted, this->cameraMatrix, this->distortionCoefficients);
	return undistorted;
}