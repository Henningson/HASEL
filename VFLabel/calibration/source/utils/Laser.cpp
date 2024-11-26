#include "utils/Laser.h"

Laser::Laser() {
	this->width = 1;
	this->height = 1;
	this->rotationVec = cv::Vec3f(0.0, 0.0, 0.0);
	this->translationVec = cv::Vec3f(0.0, 0.0, 1.0);
	this->offsets = cv::Mat::zeros(1, 1, CV_64F);
	this->vectorField = cv::Mat::zeros(1, 1, CV_64FC3);
}

Laser::Laser(std::string path) {
	this->loadFromFile(path);
}

Laser::Laser(int width, double alpha, cv::Mat offsets, cv::Vec3f rotation, cv::Vec3f translation) {
	this->buildVectorField(width, width, alpha);
	this->width = width;
	this->height = width;
	this->rotationVec = rotation;
	this->translationVec = translation;
	this->offsets = offsets.empty() ? cv::Mat::zeros(height, width, this->vectorField.type()) : offsets;
}

Laser::Laser(int width, int height, double alpha, cv::Mat offsets, cv::Vec3f rotation, cv::Vec3f translation) {
	this->buildVectorField(width, height, alpha);
	this->width = width;
	this->height = height;
	this->rotationVec = rotation;
	this->translationVec = translation;
	this->offsets = offsets.empty() ? cv::Mat::zeros(height, width, this->vectorField.type()) : offsets;
}

void Laser::loadFromFile(std::string path) {
	cv::FileStorage fs(path, cv::FileStorage::READ);
	fs["Width"] >> this->width;
	fs["Height"] >> this->height;
	fs["RotationVec"] >> this->rotationVec;
	fs["TranslationVec"] >> this->translationVec;
	fs["Offsets"] >> this->offsets;
	fs.release();
}

void Laser::saveToFile(std::string path) {
	cv::FileStorage fs(path, cv::FileStorage::WRITE);
	fs << "Width" << this->width;
	fs << "Height" << this->height;
	fs << "RotationVec" << this->rotationVec;
	fs << "TranslationVec" << this->translationVec;
	fs << "Offsets" << this->offsets;
	fs.release();
}

cv::Vec3f Laser::getVec(int x, int y) {
	return this->vectorField.col(x * 3 + y);
}

cv::Mat Laser::getField() {
	return this->vectorField;
}

int Laser::getWidth() {
	return this->width;
}

int Laser::getHeight() {
	return this->height;
}

cv::Vec3f Laser::getRotation() {
	return this->rotationVec;
}

cv::Mat Laser::getRotationMat() {
	cv::Mat rotationMat;
	cv::Rodrigues(this->rotationVec, rotationMat);
	return rotationMat;
}

cv::Vec3f Laser::getTranslation() {
	return this->translationVec;
}

void Laser::buildVectorField(int width, int height, double alpha) {
	this->vectorField = cv::Mat(3, width*height, CV_64F);

	for (int y = 0; y < height; y++) {
		for (int x = 0; x < width; x++) {
			this->vectorField.at<double>(0, 3 * x + y) = std::tan((x - (width / 2.0)) * alpha);
			this->vectorField.at<double>(1, 3 * x + y) = std::tan((y - (height / 2.0)) * alpha);
			this->vectorField.at<double>(2, 3 * x + y) = 1.0;
		}
	}
}