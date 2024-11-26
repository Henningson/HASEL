#include "calibration/LaserOptimization.h"

LaserOptimizer::LaserOptimizer(Laser& laserField, const std::vector<cv::Mat>& laserPoints3D, const std::vector<std::vector<cv::Vec3f>>& gridPositions) {
	this->gridPositions = gridPositions;
	this->vectorField = laserField;
	this->laserPoints3D = laserPoints3D;
	
	for (cv::Mat rayPoints : laserPoints3D)
		this->nrObservations += rayPoints.cols;
}

Laser LaserOptimizer::optimize(cv::Vec3f startTranslation, cv::Vec3f startRotation, double startAlpha) {
	ceres::Problem problem;

	Eigen::Matrix<double, 7, 1> data;
	data[0] = startTranslation[0];
	data[1] = startTranslation[1];
	data[2] = startTranslation[2];
	data[3] = startRotation[0];
	data[4] = startRotation[1];
	data[5] = startRotation[2];
	data[6] = startAlpha;

	for (int i = 0; i < laserPoints3D.size(); i++) {
		for (int j = 0; j < laserPoints3D.at(i).cols; j++) {
			Eigen::Vector3d point3D = Eigen::Vector3d(laserPoints3D.at(i).at<double>(0, j), laserPoints3D.at(i).at<double>(1, j), laserPoints3D.at(i).at<double>(2, j));

			ceres::CostFunction* costFunction = new ceres::AutoDiffCostFunction<Vec2VecError, 1, 7>(
				new Vec2VecError(point3D, gridPositions.at(i).at(j)[0], gridPositions.at(i).at(j)[1], this->vectorField.getWidth(), this->vectorField.getHeight()));
			problem.AddResidualBlock(costFunction, NULL, data.data());
		}
	}

	ceres::Solver::Options options;
	options.max_num_iterations = 500;
	options.trust_region_strategy_type = ceres::LEVENBERG_MARQUARDT;
	options.minimizer_progress_to_stdout = true;
	ceres::Solver::Summary summary;
	ceres::Solve(options, &problem, &summary);
	std::cout << summary.BriefReport() << "\n";
	std::cout <<  "Translation before " << startTranslation << " after " << data[0] << " " << data[1] << " " << data[2] << std::endl;
	std::cout << "Rotation before " << startRotation << " after " << data[3] << " " << data[4] << " " << data[5] << std::endl;
	std::cout << "Alpha before " << startAlpha << " after " << data[6] << std::endl;

	return Laser(this->vectorField.getWidth(), this->vectorField.getHeight(), data[6], cv::Mat(), cv::Vec3f(data[3], data[4], data[5]), cv::Vec3f(data[0], data[1], data[2]));
}

double LaserOptimizer::getAlpha() {
	return this->alphaOpt;
}

cv::Vec3f LaserOptimizer::getTranslation() {
	return this->translationOpt;
}

cv::Vec3f LaserOptimizer::getRotation() {
	return this->rotationOpt;
}