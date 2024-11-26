#include "utils/PointUtils.h"

double PointUtils::getMedianOfNeighbourhoods(std::vector<cv::Point2f> points) {
	cv::Mat distances = cv::Mat(points.size(), points.size(), CV_32F);

	//TODO: Implement

	return 0.0;
}

std::vector<cv::Point2f> PointUtils::getNearestNeighbours(cv::Point2f origin, std::vector<cv::Point2f> points, int numOfNeighbours) {
	std::vector<std::pair<double, cv::Point2f>> distancePoints;
	std::vector<cv::Point2f> neighbours;

	for (cv::Point2f point : points)
		distancePoints.push_back(std::make_pair(std::abs(cv::norm(point - origin)), point));

	std::sort(distancePoints.begin(), distancePoints.end(), [](std::pair<double, cv::Point2f> const& a, std::pair<double, cv::Point2f> const& b) {return a.first < b.first; });

	for (int i = 0; i < numOfNeighbours; i++) {
		neighbours.push_back(distancePoints.at(i + 1).second);
	}

	return neighbours;
}

std::vector<cv::Point2f> PointUtils::sortByDistance(cv::Point2f compare, std::vector<cv::Point2f> points) {
	std::vector<std::pair<double, cv::Point2f>> distancePoints;
	std::vector<cv::Point2f> neighbours;

	for (cv::Point2f point : points)
		distancePoints.push_back(std::make_pair(std::abs(cv::norm(point - compare)), point));

	std::sort(distancePoints.begin(), distancePoints.end(), [](std::pair<double, cv::Point2f> const& a, std::pair<double, cv::Point2f> const& b) {return a.first < b.first; });

	for (int i = 0; i < distancePoints.size(); i++)
		neighbours.push_back(distancePoints.at(i).second);

	return neighbours;
}

cv::Mat PointUtils::skewSymmetricMatrix(cv::Mat vec) {

	cv::Mat skewSym = cv::Mat::zeros(vec.rows, vec.rows, vec.type());
	skewSym.at<double>(0, 0) = 0.0;
	skewSym.at<double>(0, 1) = -vec.at<double>(2, 0);
	skewSym.at<double>(0, 2) = vec.at<double>(1, 0);

	skewSym.at<double>(1, 0) = vec.at<double>(2, 0);
	skewSym.at<double>(1, 1) = 0.0;
	skewSym.at<double>(1, 2) = -vec.at<double>(0, 0);

	skewSym.at<double>(2, 0) = -vec.at<double>(1, 0);
	skewSym.at<double>(2, 1) = vec.at<double>(0, 0);
	skewSym.at<double>(2, 2) = 0.0;
	return skewSym;
}

std::pair<std::vector<cv::Point2f>, std::vector<double>> PointUtils::normalizedHoughTransform(const cv::Mat& image, const std::vector<cv::Point2f>& cornerPoints, bool filter) {
	std::vector<cv::Point2f> houghSpace;
	std::vector<double> lineLength;

	auto im = image.clone();
	for (cv::Point2f point : cornerPoints) {
		auto neighbours = PointUtils::getNearestNeighbours(point, cornerPoints, 4);

		for (auto neighbour : neighbours) {
			cv::Point2f firstQuadrantVec = cv::Point2f(std::abs(neighbour.x), std::abs(neighbour.y));

			double angle = std::atan2(std::abs(point.y - neighbour.y), std::abs(point.x - neighbour.x));
			if (angle < 0.0)
				angle += 2 * M_PI;
			houghSpace.push_back(cv::Point2f(angle * 180.0 / M_PI, std::abs(cv::norm(neighbour - point))));
		}
	}

	//Houhspace, remove angles that are rougly 45�
	if (filter) {
		for (cv::Point2f point : houghSpace) {
			houghSpace.erase(
				std::remove_if(
					houghSpace.begin(),
					houghSpace.end(),
					[](cv::Point2f const& point) {
						return std::abs(point.x - 45.0) < 10.0 || point.y > 30.0; }
				),
				houghSpace.end()
							);
		}
	}

	cv::Mat bestLabels, clusterCenter;
	cv::kmeans(houghSpace, 2, bestLabels, cv::TermCriteria(cv::TermCriteria::EPS + cv::TermCriteria::COUNT, 10, 1.0), 15, cv::KMEANS_PP_CENTERS, clusterCenter);

	auto len1 = clusterCenter.at<float>(0, 1);
	auto len2 = clusterCenter.at<float>(1, 1);

	cv::Point2f vec1 = cv::Point2f(std::cos(clusterCenter.at<float>(0, 0) / 180.0 * M_PI), std::sin(clusterCenter.at<float>(0, 0) / 180.0 * M_PI));
	cv::Point2f vec2 = cv::Point2f(std::cos(clusterCenter.at<float>(1, 0) / 180.0 * M_PI), std::sin(clusterCenter.at<float>(1, 0) / 180.0 * M_PI));

	if (vec2.x > vec1.x) {
		auto temp = vec1;
		vec1 = vec2;
		vec2 = temp;
		lineLength.push_back(len2);
		lineLength.push_back(len1);
	}
	else {
		lineLength.push_back(len1);
		lineLength.push_back(len2);
	}

	//Why is this necessary?
	vec1.y = -vec1.y;
	return std::make_pair(std::vector<cv::Point2f>{ vec1, vec2 }, lineLength);
}


std::vector<cv::Vec2f> PointUtils::matToVec2(cv::Mat mat) {
	if (mat.rows != 2)
		return std::vector<cv::Vec2f>();

	std::vector<cv::Vec2f> vecs;
	for (int x = 0; x < mat.cols; x++) {
		cv::Vec2f temp;
		temp[0] = mat.at<double>(0, x);
		temp[1] = mat.at<double>(1, x);
		vecs.push_back(temp);
	}
	return vecs;
}

std::vector<cv::Vec3f> PointUtils::matToVec3(cv::Mat mat) {
	if (mat.rows != 3)
		return std::vector<cv::Vec3f>();

	std::vector<cv::Vec3f> vecs;
	for (int x = 0; x < mat.cols; x++) {
		cv::Vec3f temp;
		temp[0] = mat.at<double>(0, x);
		temp[1] = mat.at<double>(1, x);
		temp[2] = mat.at<double>(2, x);
		vecs.push_back(temp);
	}
	
	return vecs;
}

cv::Mat PointUtils::vec2ToMat(std::vector<cv::Vec2f> vec) {
	cv::Mat m = cv::Mat::zeros(2, vec.size(), CV_64F);
	for (int i = 0; i < vec.size(); i++) {
		m.at<double>(0, i) = vec.at(i)[0];
		m.at<double>(1, i) = vec.at(i)[1];
	}
	return m;
}

cv::Mat PointUtils::vec3ToMat(std::vector<cv::Vec3f> vec) {
	cv::Mat m = cv::Mat::zeros(3, vec.size(), CV_64F);
	for (int i = 0; i < vec.size(); i++) {
		m.at<double>(0, i) = vec.at(i)[0];
		m.at<double>(1, i) = vec.at(i)[1];
		m.at<double>(2, i) = vec.at(i)[2];
	}
	return m;
}