#include "utils/CurveFitting.h"


double polyeval(Eigen::VectorXd coeffs, double x) {
	double result = 0.0;
	for (int i = 0; i < coeffs.size(); i++) { result += coeffs[i] * pow(x, i); }
	return result;
}

Eigen::VectorXd polyfit(Eigen::VectorXd xvals, Eigen::VectorXd yvals, int order) {
	assert(xvals.size() == yvals.size());
	assert(order >= 1 && order <= xvals.size() - 1);
	Eigen::MatrixXd A(xvals.size(), order + 1);
	for (int i = 0; i < xvals.size(); i++) {
		A(i, 0) = 1.0;
	}
	for (int j = 0; j < xvals.size(); j++) {
		for (int i = 0; i < order; i++) {
			A(j, i + 1) = A(j, i) * xvals(j);
		}
	}
	auto Q = A.householderQr();
	auto result = Q.solve(yvals);
	return result;
}

//Get f(x) through y = mx + b 
double getY(cv::Vec4f line, double x) {
	return (line[1] / line[0]) * (x - line[2]) + line[3];
}

std::pair<cv::Mat, cv::Mat> fitRay(cv::Mat laserPoints) {
	cv::Mat centroid;
	cv::reduce(laserPoints, centroid, 1, cv::REDUCE_AVG);

	laserPoints = laserPoints - cv::repeat(centroid, 1, laserPoints.cols);
	cv::Mat covariance = laserPoints * laserPoints.t();
	cv::Mat eigenvalue, eigenvector;
	cv::eigen(covariance, eigenvalue, eigenvector);
	return std::make_pair(centroid, eigenvector.col(2));
}
