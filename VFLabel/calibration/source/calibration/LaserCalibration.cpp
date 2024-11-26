#include "calibration/LaserCalibration.h"

LaserCalibration::LaserCalibration(std::vector<cv::Mat> images, std::vector<std::filesystem::path> filenames, double gridDistance, Laser laser, Camera camera)
	: Calibration(images, filenames, gridDistance) {
	this->gridSize = gridSize;
	this->useImage = std::vector<bool>(images.size(), false);
	this->laser = laser;
	this->camera = camera;
}

void LaserCalibration::calibrate() {
	std::vector<cv::Mat> homographiesCheckerboard;

	int i = 0;
	for (cv::Mat image : this->images) {
		cv::Mat bwImage = this->preprocessImage(image);
		cv::Mat copy = image.clone();

		cv::Mat checkerboardROI = this->extractCheckerboardROI(bwImage);
		cv::imshow("CBROI", checkerboardROI);
		cv::waitKey(1);

		cv::Mat checkerboardImage;
		IMUtils::imadjust(bwImage, checkerboardImage, 0.00, 0.5, 0.0, 1.0);

		cv::Mat bilateralFiltered;
		cv::bilateralFilter(checkerboardImage, bilateralFiltered, 20, 50.0, 50.0);
		cv::Mat laserROI = this->extractLaserROI(bwImage);
		cv::Mat laserImage;
		IMUtils::imadjust(bwImage, laserImage, 0.7, 1.0, 0.0, 1.0);

		this->gradientSize = 3;
		this->qualityLevel = 0.000001;
		std::vector<cv::Point2f> laserCorners = this->getCorners(laserImage, laserROI, 5, this->laser.getHeight() * this->laser.getWidth());
		this->gradientSize = 3;
		this->qualityLevel = 0.004;
		std::vector<cv::Point2f> checkerboardCorners = this->getCorners(bilateralFiltered, checkerboardROI, 8, 15000);


		for (cv::Point2f cbCorner : checkerboardCorners)
			cv::circle(copy, cbCorner, 3, cv::Scalar(0, 0, 255), -1);

		removeCornersAtPerimeter(checkerboardCorners, checkerboardROI, 20.0);

		for (cv::Point2f laserCorner : laserCorners)
			cv::circle(copy, laserCorner, 3, cv::Scalar(255, 0, 0), -1);

		for (cv::Point2f cbCorner : checkerboardCorners)
			cv::circle(copy, cbCorner, 3, cv::Scalar(0, 255, 0), -1);

		auto laserPoints = this->getPixelGridCorrespondences(laserCorners, 6.0, image, false);
		auto checkerboardPoints = this->getPixelGridCorrespondences(checkerboardCorners, 6.0, image, false);

		if (laserPoints.first.size() < 15 || laserPoints.second.size() < 15 || checkerboardPoints.first.size() < 15 || checkerboardPoints.second.size() < 15 ||
			laserPoints.first.size() != laserPoints.second.size() || checkerboardPoints.first.size() != checkerboardPoints.second.size()) {
			i++;
			continue;
		}

		cv::imshow("bla", copy);
		cv::waitKey(1);

		this->useImage.at(i) = true;
		this->checkerboardHomographies.push_back(cv::findHomography(checkerboardPoints.first, checkerboardPoints.second, cv::RANSAC));
		this->laserCorrespondences.addGridPixelCorrespondences(laserPoints.first, laserPoints.second);
		this->checkerboardCorrespondences.addGridPixelCorrespondences(checkerboardPoints.first, checkerboardPoints.second);
		i++;
	}

	cv::destroyAllWindows();

	this->estimateLaserPosition();
}

Laser LaserCalibration::getLaser() {
	return this->laser;
}

Correspondences LaserCalibration::getLaserCorrespondences() {
	return this->laserCorrespondences;
}

Correspondences LaserCalibration::getCheckerboardCorrespondences() {
	return this->checkerboardCorrespondences;
}

std::vector<cv::Mat> LaserCalibration::getCheckerboardHomographies() {
	return this->checkerboardHomographies;
}

void LaserCalibration::estimateLaserPosition() {

	//Recalculate extrinsic parameters
	cv::Mat stddevIntrinsic;
	cv::Mat stddevExtrinsic;
	cv::Mat newPoints;
	cv::Mat perViewError;
	std::vector<cv::Mat> translationVecs;
	std::vector<cv::Mat> rotationVecs;

	auto reprojError = cv::calibrateCameraRO(this->checkerboardCorrespondences.getGrid(), this->checkerboardCorrespondences.getPixels(), this->camera.getImageSize(), 0, this->camera.getCameraMatrix(), this->camera.getDistortionCoefficients(), rotationVecs, translationVecs, newPoints, 
		cv::CALIB_FIX_INTRINSIC | cv::CALIB_FIX_K1 | cv::CALIB_FIX_K2 | cv::CALIB_FIX_K3 | cv::CALIB_FIX_K4 | cv::CALIB_FIX_K5 | cv::CALIB_FIX_K6 | cv::CALIB_USE_INTRINSIC_GUESS | cv::CALIB_USE_LU);

	std::vector<cv::Mat> laser3DCoordinates = this->triangulate(this->checkerboardHomographies, this->laserCorrespondences, translationVecs, rotationVecs);
	
	//Gather all 3D-Values corresponding to a specific grid-point
	//As we ordered the grids already, no further sorting is necessary

	cv::Mat rayOrigins = cv::Mat(this->laser.getHeight(), this->laser.getWidth(), CV_64FC3);
	cv::Mat rayDirections = cv::Mat(this->laser.getHeight(), this->laser.getWidth(), CV_64FC3);

	cv::Mat laserOrigin = this->getLaserOrigin(laserCorrespondences, laser3DCoordinates);
	cv::Mat laserRotation = this->getLaserRotation(laserOrigin);

	LaserOptimizer laserOptim = LaserOptimizer(this->laser, laser3DCoordinates, this->laserCorrespondences.getGrid());
	this->laser = laserOptim.optimize(laserOrigin, laserRotation, 0.01);
}

cv::Mat LaserCalibration::preprocessImage(cv::Mat& image) {
	cv::Mat grayImage;
	cv::cvtColor(image, grayImage, cv::COLOR_BGR2GRAY);
	return grayImage;
}

cv::Mat LaserCalibration::generateMask(cv::Mat& image, cv::Mat& stats) {
	return cv::Mat();
}

std::vector<cv::Vec4i> LaserCalibration::getLines(cv::Mat& image) {
	return std::vector<cv::Vec4i>();
}

std::pair<cv::Mat, cv::Mat> LaserCalibration::getStats(cv::Mat& image) {
	cv::Mat labelImage, stats, centroids;

	int numLabels = cv::connectedComponentsWithStats(image, labelImage, stats, centroids);

	cv::Mat idx;
	cv::sortIdx(stats.col(4), idx, cv::SORT_EVERY_COLUMN + cv::SORT_ASCENDING);
	cv::Mat sorted_stats = cv::Mat(0, 5, stats.type());
	cv::Mat sorted_centroids = cv::Mat(0, 2, centroids.type());
	int median = stats.at<int>(idx.at<int>(stats.rows / 2), 4);

	for (int i = 0; i < stats.rows; i++) {
		sorted_stats.push_back(stats.row(idx.at<int>(i)));
		sorted_centroids.push_back(centroids.row(idx.at<int>(i)));
	}

	return std::make_pair(sorted_stats, sorted_centroids);
}

std::vector<cv::Point2f> LaserCalibration::getCorners(const cv::Mat& image, const cv::Mat& mask, int minDistance, int maxCorners) {
	cv::Mat out;
	cv::multiply(image, mask / 255, out);
	std::pair<cv::Mat, cv::Mat> stats = this->getStats(out);

	std::vector<cv::Point2f> corners;
	cv::goodFeaturesToTrack(image, corners, maxCorners, this->qualityLevel, 15, mask / 255, 5, this->gradientSize, this->useHarrisDetector, this->harrisKValue);
	cv::cornerSubPix(image, corners, cv::Size(13, 13), cv::Size(-1, -1), cv::TermCriteria(cv::TermCriteria::EPS + cv::TermCriteria::COUNT, 40, 0.001));
	return corners;
}

void LaserCalibration::validateCorners(std::vector<cv::Point2f>& corners, const cv::Mat& image, double medianDistance) {
	corners.erase(
		std::remove_if(
			corners.begin(),
			corners.end(),
			[image, medianDistance](cv::Point2f const& corner) {
				int x = corner.x - medianDistance * 0.75;
				int y = corner.y - medianDistance * 0.75;
				int width = medianDistance * 0.75;
				int height = medianDistance * 0.75;

				if (x < 0 || y < 0 || x + width > image.cols || y + height > image.rows)
					return true;

				cv::Rect rect = cv::Rect(x, y, width, height);
				cv::Mat crop = image(rect);
				cv::threshold(crop, crop, 0, 1, cv::THRESH_BINARY | cv::THRESH_OTSU);
				return std::abs(cv::mean(crop)[0] - 0.5) > 0.2; }
		),
		corners.end()
	);
}

void LaserCalibration::removeCornersAtPerimeter(std::vector<cv::Point2f>& corners, const cv::Mat& checkerboardROI, double minDistanceAllowed) {
	std::vector<std::vector<cv::Point>> contours;
	cv::findContours(checkerboardROI, contours, cv::RETR_TREE, cv::CHAIN_APPROX_SIMPLE);
	
	for (std::vector<cv::Point> contour : contours) {
		corners.erase(
			std::remove_if(
				corners.begin(),
				corners.end(),
				[contour, minDistanceAllowed](cv::Point2f const& corner) {
					return std::abs(cv::pointPolygonTest(contour, corner, true)) < minDistanceAllowed; }
			),
			corners.end()
						);
	}
}

std::pair<std::vector<cv::Vec3f>, std::vector<cv::Vec2f>> LaserCalibration::getPixelGridCorrespondences(std::vector<cv::Point2f> pixelCoordinates, double distanceThreshold, cv::Mat& image, bool isLaser) {
	auto unitVectorAndLengthCB = PointUtils::normalizedHoughTransform(image, pixelCoordinates, true);

	cv::Point2f principalAxis1 = unitVectorAndLengthCB.first[0] * unitVectorAndLengthCB.second[0];
	cv::Point2f principalAxis2 = unitVectorAndLengthCB.first[1] * unitVectorAndLengthCB.second[1];
	auto cloneImage = image.clone();

	if (isLaser)
		principalAxis2.x = -principalAxis2.x;

	CorrespondenceMatcher corresMatch = CorrespondenceMatcher(pixelCoordinates, principalAxis1, principalAxis2, 2.0, distanceThreshold, image);
	auto corres = corresMatch.getPixelGridCorrespondences();

	if (isLaser) {
		int keyPress = 0;
		do {

			if ((char)keyPress == 27)
				break;

			cv::Point2f direction = cv::Point2f(0, 0);
			cloneImage = image.clone();
			switch ((char)keyPress) {
			case 37:
				direction = cv::Point2f(-1, 0);
				break;
			case 38:
				direction = cv::Point2f(0, -1);
				break;
			case 39:
				direction = cv::Point2f(1, 0);
				break;
			case 40:
				direction = cv::Point2f(0, 1);
				break;
			}

			for (int i = 0; i < corres.first.size(); i++)
				corres.first.at(i) += direction;

			for (int i = 0; i < corres.second.size(); i++) {
				cv::circle(cloneImage, corres.second.at(i), 3, cv::Scalar(0, 255, 0), -1);
				cv::putText(cloneImage, "(" + std::to_string((int)corres.first.at(i).x) + ", " + std::to_string((int)corres.first.at(i).y) + ")", corres.second.at(i), 1, 0.8, cv::Scalar(255, 255, 255));
			}

			cv::line(cloneImage, pixelCoordinates.at(0), pixelCoordinates.at(0) + principalAxis1, cv::Scalar(0, 255, 0), 2);
			cv::line(cloneImage, pixelCoordinates.at(0), pixelCoordinates.at(0) + principalAxis2, cv::Scalar(0, 0, 255), 2);
			cv::imshow("Grid Correspondences", cloneImage);
			keyPress = cv::waitKey(0);

		} while ((char)keyPress != 27);
	}

	for (int i = 0; i < corres.second.size(); i++) {
		cv::circle(image, corres.second.at(i), 3, cv::Scalar(0, 255, 0), -1);
		cv::putText(image, "(" + std::to_string((int)corres.first.at(i).x) + ", " + std::to_string((int)corres.first.at(i).y) + ")", corres.second.at(i), 1, 0.8, cv::Scalar(255, 255, 255));
	}

	cv::line(image, pixelCoordinates.at(0), pixelCoordinates.at(0) + principalAxis1, cv::Scalar(0, 255, 0), 2);
	cv::line(image, pixelCoordinates.at(0), pixelCoordinates.at(0) + principalAxis2, cv::Scalar(0, 0, 255), 2);
	cv::imshow("Grid Correspondences", image);
	cv::waitKey(1);
	
	std::vector<cv::Vec3f> gridCoords;
	std::vector<cv::Vec2f> pixelCoords;
	for (int i = 0; i < corres.first.size(); i++) {
		gridCoords.push_back(cv::Vec3f(corres.first.at(i).x, corres.first.at(i).y, 0.0));
		pixelCoords.push_back(cv::Vec2f(corres.second.at(i).x, corres.second.at(i).y));
	}

	return std::make_pair(gridCoords, pixelCoords);
}

cv::Mat LaserCalibration::extractLaserROI(const cv::Mat& image) {
	cv::Mat copy = image.clone();
	IMUtils::imadjust(image, copy, 0.6, 1.0, 0.0, 1.0);
	cv::Mat se_th_cb = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(9, 9));
	cv::morphologyEx(copy, copy, cv::MORPH_TOPHAT, se_th_cb);
	cv::threshold(copy, copy, 0, 255, cv::THRESH_BINARY | cv::THRESH_OTSU);
	cv::morphologyEx(copy, copy, cv::MORPH_DILATE, cv::getStructuringElement(cv::MORPH_RECT, cv::Size(9, 9)));
	return copy;
}

cv::Mat LaserCalibration::extractCheckerboardROI(const cv::Mat& image) {
	cv::Mat morphRectSmall = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(3, 3));
	cv::Mat morphRectMid = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(9, 9));
	cv::Mat morphRectBig = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(image.rows / 8, image.cols / 8));

	cv::Mat grayImage = image.clone();
	IMUtils::imadjust(grayImage, grayImage, 0.00, 0.4, 0.0, 1.0);
	//TODO: Add homomorphic filter similar to the MATLAB Implementation here.

	cv::Mat out;
	cv::morphologyEx(grayImage, out, cv::MORPH_BLACKHAT, morphRectBig);
	out.convertTo(out, -1, 2, 0);

	cv::Mat bw = cv::Mat::zeros(grayImage.size(), CV_8U);
	cv::threshold(out, bw, 0, 255, cv::THRESH_BINARY | cv::THRESH_OTSU);
	cv::morphologyEx(bw, bw, cv::MORPH_OPEN, morphRectSmall);

	cv::morphologyEx(bw, bw, cv::MORPH_DILATE, morphRectMid);
	
	cv::Mat contourImage = cv::Mat::zeros(bw.size(), CV_8U);
	std::vector<std::vector<cv::Point>> contours;
	cv::findContours(bw, contours, cv::RETR_LIST, cv::CHAIN_APPROX_SIMPLE);
	
	double maxArea = 0.0;
	int contourID = 0;
	for (int i = 0; i < contours.size(); i++) {
		double area = cv::contourArea(contours[i]);
		if (area > maxArea) {
			maxArea = area;
			contourID = i;
		}
	}

	cv::drawContours(contourImage, contours, contourID, cv::Scalar(255), -1);
	cv::morphologyEx(contourImage, contourImage, cv::MORPH_DILATE, morphRectMid);
	cv::morphologyEx(contourImage, contourImage, cv::MORPH_DILATE, morphRectMid);

	return contourImage;
}

std::vector<cv::Mat> LaserCalibration::triangulate(const std::vector<cv::Mat>& homographies, Correspondences& laserCorrespondences, const std::vector<cv::Mat>& translationVecs, const std::vector<cv::Mat>& rotationVecs) {
	std::vector<cv::Mat> laser3DCoordinates;
	for (int i = 0; i < homographies.size(); i++) {
		cv::Mat vecMat = cv::Mat(3, laserCorrespondences.getPixelsAt(i).size(), CV_64F);
		int numOfPoints = laserCorrespondences.getPixelsAt(i).size();

		for (int j = 0; j < numOfPoints; j++) {
			vecMat.at<double>(0, j) = laserCorrespondences.getPixelPoint(i, j)[0];
			vecMat.at<double>(1, j) = laserCorrespondences.getPixelPoint(i, j)[1];
			vecMat.at<double>(2, j) = 1.0;
		}

		cv::Mat m = checkerboardHomographies.at(i).inv() * vecMat;
		cv::Mat normalisation = cv::repeat(m.row(2), 3, 1);
		m = m / normalisation;
		m.row(2).setTo(cv::Scalar(0.0));
		cv::Mat rotationMat;
		cv::Rodrigues(rotationVecs.at(i), rotationMat);
		m = rotationMat * m;
		m = m + cv::repeat(translationVecs.at(i), 1, numOfPoints);
		laser3DCoordinates.push_back(m);
	}
	return laser3DCoordinates;
}

cv::Mat getPointwiseDistances(cv::Mat a, cv::Mat b) {
	cv::Mat distances = cv::Mat(b.cols, a.cols, CV_64F);
	for (int y = 0; y < distances.rows; y++) {
		for (int x = 0; x < distances.cols; x++) {
			auto ACol = a.col(x);
			auto BCol = b.col(y);
			auto c = cv::norm(ACol - BCol);
			distances.at<double>(y, x) = c;
		}
	}

	return distances;
}

void drawMat(cv::Mat& image, cv::Mat points, cv::Scalar color) {
	for (int i = 0; i < points.cols; i++)
		cv::circle(image, cv::Point(points.at<double>(0, i), points.at<double>(1, i)), 3, color, -1);
}

std::pair<std::vector<cv::Vec3f>, std::vector<cv::Vec2f>> LaserCalibration::fitGrid(std::pair<std::vector<cv::Vec3f>, std::vector<cv::Vec2f>> origin, std::pair<std::vector<cv::Vec3f>, std::vector<cv::Vec2f>> toFit) {
	cv::Mat originGrid = PointUtils::vec3ToMat(origin.first);
	cv::Mat originPixel = PointUtils::vec2ToMat(origin.second);
	cv::Mat toFitGrid = PointUtils::vec3ToMat(toFit.first);
	cv::Mat toFitPixel = PointUtils::vec2ToMat(toFit.second);
	toFitGrid.convertTo(toFitGrid, CV_64F);
	originPixel.convertTo(originPixel, CV_64F);
	cv::Mat homOriginPixelToGrid = cv::findHomography(origin.first, origin.second);
	cv::Mat homFitPixelToGrid = cv::findHomography(toFit.first, toFit.second);

	cv::Mat topLeftCoordinate = cv::Mat(3, 1, CV_64F);
	topLeftCoordinate.at<double>(0, 0) = origin.second.at(0)[0];
	topLeftCoordinate.at<double>(1, 0) = origin.second.at(1)[0];
	topLeftCoordinate.at<double>(2, 0) = 0.0;

	cv::Mat image = cv::Mat::zeros(768, 768, CV_8UC3);
	drawMat(image, originPixel, cv::Scalar(255, 255, 255));

	int referenceWidth = std::sqrt(toFitGrid.cols) / 2;
	cv::Mat baseGrid = cv::Mat::zeros(3, referenceWidth * referenceWidth, CV_64F);
	for (int y = 0; y < referenceWidth; y++) {
		for (int x = 0; x < referenceWidth; x++) {
			baseGrid.at<double>(0, y * referenceWidth + x) = double(x);
			baseGrid.at<double>(1, y * referenceWidth + x) = double(y);
			baseGrid.at<double>(2, y * referenceWidth + x) = 1.0;
		}
	}


	cv::Mat basePixel = homOriginPixelToGrid * baseGrid;
	basePixel /= cv::repeat(basePixel.row(2), 3, 1);


	cv::Mat referenceBaseGrid = baseGrid.clone();
	cv::Mat referenceBasePixel = homFitPixelToGrid * referenceBaseGrid;
	referenceBasePixel /= cv::repeat(referenceBasePixel.row(2), 3, 1);
	
	cv::Mat optimReferenceGrid = referenceBaseGrid.clone();
	cv::Mat optimReferencePixel = referenceBasePixel.clone();

	cv::Mat directionMat = (cv::Mat_<double>(3, 4) << 0.0, 0.0, 1.0, -1.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);


	double errorEstimate = 10000000000.0;
	int iter = 0;
	double distanceThreshold = 15.0;
	while (iter < 500) {

		cv::Mat sumErrors = cv::Mat(1, 4, CV_64F); // Mean error for every direction
		cv::Mat numberOfGoodPoints = cv::Mat(1, 4, CV_8U); // Kein Plan
		for (int i = 0; i < 4; i++) {

			cv::Mat moveOptimReferenceGrid = optimReferenceGrid + cv::repeat(directionMat.col(i), 1, optimReferenceGrid.cols);
			cv::Mat moveOptimReferencePixel = homFitPixelToGrid * moveOptimReferenceGrid;
			moveOptimReferencePixel /= cv::repeat(moveOptimReferencePixel.row(2), 3, 1);

			cv::Mat homBasePxToMovedPx = cv::findHomography(PointUtils::matToVec3(basePixel), PointUtils::matToVec2(moveOptimReferencePixel.rowRange(cv::Range(0,2))));
			cv::Mat m = homBasePxToMovedPx * referenceBasePixel;
			m /= cv::repeat(m.row(2), 3, 1);

			originPixel.convertTo(originPixel, CV_64F);
			m.convertTo(m, CV_64F);
			cv::Mat distances = getPointwiseDistances(originPixel, m.rowRange(cv::Range(0, 2)));

			cv::reduce(distances, distances, 1, cv::REDUCE_MIN);
			std::cout << distances << std::endl;
			cv::Mat numSmallerThreshold = distances < distanceThreshold;
			std::cout << numSmallerThreshold << std::endl;
			cv::Scalar numOfGoodPoints = cv::sum(numSmallerThreshold/255);
			cv::Mat singleValMat;
			cv::reduce(distances, singleValMat, 0, cv::REDUCE_SUM);
			sumErrors.at<double>(0, i) = singleValMat.at<double>(0, 0);
			numberOfGoodPoints.at<uchar>(0, i) = (uchar)numOfGoodPoints[0];
		}
		double minVal, maxVal;
		cv::Point minID, maxID;
		cv::minMaxLoc(sumErrors, &minVal, &maxVal, &minID, &maxID);

		double average = sumErrors.at<double>(minID) / (double)numberOfGoodPoints.at<uchar>(minID);

		numberOfGoodPoints.convertTo(numberOfGoodPoints, CV_64F);
		cv::Scalar good = cv::sum((sumErrors / numberOfGoodPoints) > errorEstimate);
		if (good[0] == 0.0)
			break; //Minimum found

		errorEstimate = average;
		optimReferenceGrid = optimReferenceGrid + cv::repeat(directionMat.col(minID.x), 1, optimReferenceGrid.cols);
		optimReferencePixel = homFitPixelToGrid * optimReferenceGrid;
		optimReferencePixel /= cv::repeat(optimReferencePixel.row(2), 3, 1);
		iter += 1;
	}

	drawMat(image, optimReferencePixel, cv::Scalar(0, 255, 0));
	cv::imshow("Reference", image);
	cv::waitKey(0);

	toFitGrid -= cv::repeat(optimReferenceGrid.col(0), 1, toFitGrid.cols);
	toFitGrid += cv::repeat(topLeftCoordinate, 1, toFitGrid.cols);
	std::vector<cv::Vec3f> convertFitGrid = PointUtils::matToVec3(toFitGrid);
	return std::make_pair(convertFitGrid, toFit.second);;
}

cv::Mat LaserCalibration::getLaserOrigin(Correspondences& laserCorrespondences, std::vector<cv::Mat>& laser3DCoordinates) {
	std::vector<cv::Mat> ordered3DLocations;
	std::vector<std::pair<cv::Mat, cv::Mat>> rays;
	cv::Mat rayMat;
	cv::Mat skewSymMat;
	cv::Mat b;

	bool startSkewSymm = true;
	for (int y = 0; y < this->laser.getWidth(); y++) {
		for (int x = 0; x < this->laser.getHeight(); x++) {
			cv::Mat points3D = cv::Mat(3, 1, CV_64F);
			bool startPoints3D = true;
			for (int i = 0; i < laserCorrespondences.getGrid().size(); i++) {
				for (int j = 0; j < laserCorrespondences.getGridAt(i).size(); j++) {
					if (laserCorrespondences.getGridPoint(i, j) == cv::Vec3f(x, y, 0.0)) {
						if (startPoints3D) {
							points3D = laser3DCoordinates.at(i).col(j);
							startPoints3D = false;
						}
						cv::hconcat(points3D, laser3DCoordinates.at(i).col(j), points3D);
						break;
					}
				}
			}
			ordered3DLocations.push_back(points3D);


			std::pair<cv::Mat, cv::Mat> ray = fitRay(points3D);
			rays.push_back(ray);


			if (startSkewSymm) {
				startSkewSymm = false;
				skewSymMat = PointUtils::skewSymmetricMatrix(ray.second);
				b = skewSymMat * ray.first;
				continue;
			}
			cv::vconcat(skewSymMat, PointUtils::skewSymmetricMatrix(ray.second), skewSymMat);
			cv::vconcat(b, PointUtils::skewSymmetricMatrix(ray.second) * ray.first, b);
		}
	}

	cv::Mat x;
	cv::solve(skewSymMat, b, x, cv::DECOMP_QR);
	cv::Mat all3DPoints;
	cv::hconcat(ordered3DLocations, all3DPoints);
	cv::Mat mean, max, min;
	cv::reduce(all3DPoints, mean, 1, cv::REDUCE_AVG);
	cv::reduce(all3DPoints, max, 1, cv::REDUCE_MAX);
	cv::reduce(all3DPoints, min, 1, cv::REDUCE_MIN);

	return mean - x;
}

cv::Mat LaserCalibration::getLaserRotation(cv::Mat laserOrigin) {
	cv::Mat unitVectorZ = cv::Mat::zeros(3, 1, CV_64F);
	unitVectorZ.at<double>(2, 0) = 1.0;
	cv::Mat rotationVec = unitVectorZ.cross(laserOrigin);
	rotationVec = rotationVec / cv::norm(rotationVec);
	auto alpha = std::acos(unitVectorZ.dot(laserOrigin) / cv::norm(laserOrigin));
	return rotationVec * alpha;
}
