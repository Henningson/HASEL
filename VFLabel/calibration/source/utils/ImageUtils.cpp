#include "utils/ImageUtils.h"

std::vector<cv::Mat> IMUtils::loadImages(std::vector<std::filesystem::path> paths, int loadOpt) {
	std::vector<cv::Mat> images;
	
	for (auto path : paths)
		images.push_back(cv::imread(path.string(), loadOpt));

	return images;
}

double IMUtils::getScreenspaceAngleOfLine(cv::Vec4i line) {
	double deltaY = double(line[1]) - double(line[3]);
	double deltaX = double(line[2]) - double(line[0]);
	double result = std::atan2(deltaY, deltaX) * (180.0 / 3.141592653589793238462643383279502884L);
	return (result < 0) ? (360.0 + result) : result;
}

void IMUtils::stretchlimFromHist(const cv::Mat& hist, double* low_value, double* high_value, double low_fract, double high_fract, unsigned int histSum) {
	CV_Assert(low_fract >= 0 && low_fract < 1.0);
	CV_Assert(low_fract < high_fract && high_fract <= 1.0);

	unsigned int sum;
	unsigned int low_count = low_fract * histSum;
	sum = 0;
	for (unsigned int i = 0; i < hist.rows; i++) {
		if (sum >= low_count) {
			*low_value = i;
			break;
		}

		sum += ((float*)hist.data)[i];
	}

	unsigned int high_count = (1 - high_fract) * histSum;
	sum = 0;
	for (unsigned int i = hist.rows - 1; i >= 0; i--) {
		if (sum >= high_count) {
			*high_value = i;
			break;
		}

		sum += ((float*)hist.data)[i];
	}
}

//TODO: surely something like this already exists
int IMUtils::bitsFromDepth(int depth) {
	if (depth == CV_8U)
		return 8;
	else if (depth == CV_16U)
		return 16;
	else
		return 0;
}

//TODO: handle RGB or force user to do a channel at a time?
void IMUtils::stretchlim(const cv::InputArray _image, double* low_value,	double* high_value, double low_fract, double high_fract) {
	cv::Mat image = _image.getMat();

	CV_Assert(image.type() == CV_8UC1 || image.type() == CV_16UC1);

	if (low_fract == 0 && high_fract == 1.0) {
		// no need to waste calculating histogram
		*low_value = 0;
		*high_value = 1;
		return;
	}

	int nPixelValues = 1 << bitsFromDepth(image.depth());
	int channels[] = { 0 };
	cv::Mat hist;
	int histSize[] = { nPixelValues };
	float range[] = { 0, (float)nPixelValues };
	const float* ranges[] = { range };
	cv::calcHist(&image, 1, channels, cv::Mat(), hist, 1, histSize, ranges);

	stretchlimFromHist(hist, low_value, high_value, low_fract, high_fract, image.rows * image.cols);

	//TODO: scaling to 0..1 here, but should be in stretchlimFromHist?
	unsigned int maxVal = (1 << bitsFromDepth(_image.depth())) - 1;
	*low_value /= maxVal;
	*high_value /= maxVal;
}

void IMUtils::imadjust(const cv::InputArray _src, cv::OutputArray _dst, double low_in, double high_in, double low_out, double high_out) {
	CV_Assert((low_in == 0 || high_in != low_in) && high_out != low_out);

	//FIXME: use NaN or something else for default values?
	if (low_in == 0 && high_in == 0)
		stretchlim(_src, &low_in, &high_in, low_out, high_out);

	double alpha = (high_out - low_out) / (high_in - low_in);
	double beta = high_out - high_in * alpha;

	cv::Mat src = _src.getMat();
	int depth;
	if (_dst.empty())
		depth = _src.depth();
	else
		depth = _dst.depth();

	//TODO: handle more than just 8U/16U
	//adjust alpha/beta to handle to/from different depths
	int max_in = (1 << bitsFromDepth(_src.depth())) - 1;
	int max_out = (1 << bitsFromDepth(_dst.depth())) - 1;
	// y = a*x*(outmax/inmax) + b*outmax
	alpha *= max_out / max_in;
	beta *= max_out;

	src.convertTo(_dst, depth, alpha, beta);
}


cv::Mat IMUtils::homomorphic(const cv::Mat& image, double gh, double gl, double d0, double c) {
	cv::Mat padded;       
	cv::Mat src = image.clone();
	src.convertTo(src, CV_32F);
	cv::log(src, src);

	int dft_M = cv::getOptimalDFTSize(src.rows);
	int dft_N = cv::getOptimalDFTSize(src.cols); // on the border add zero values
	cv::copyMakeBorder(src, padded, 0, dft_M - src.rows, 0, dft_N - src.cols, cv::BORDER_CONSTANT, cv::Scalar::all(0));
	cv::Mat planes[] = { cv::Mat_<float>(padded), cv::Mat::zeros(padded.size(), CV_32F) };
	cv::Mat complexImage;
	cv::merge(planes, 2, complexImage);         // Add to the expanded another plane with zeros
	cv::dft(complexImage, complexImage);            // this way the result may fit in the source matrix
	//IMUtils::flipQuadrants(complexImage);

	cv::Mat temp = cv::Mat(dft_M, dft_N, CV_32F);

	for (int i = 0; i < temp.rows; i++) {
		for (int j = 0; j < temp.cols; j++) {
			float d2 = std::pow((i - dft_M / 2), 2) + std::pow((j - dft_N / 2), 2);
			temp.at<float>(i, j) = (gh - gl) * (1.0 - (float)exp(-(c * d2 / (d0 * d0)))) + gl;
		}
	}

	cv::Mat comps[] = { temp, temp };
	cv::Mat filter = complexImage.clone();
	cv::merge(comps, 2, filter);
	cv::mulSpectrums(complexImage, filter, complexImage, 0);
	IMUtils::flipQuadrants(complexImage);
	cv::idft(complexImage, complexImage);
	cv::split(complexImage, planes);
	cv::normalize(planes[0], planes[0], 0, 1, cv::NORM_MINMAX);

	return planes[0];
}

void IMUtils::flipQuadrants(cv::Mat& image) {
	int cx = image.cols / 2;
	int cy = image.rows / 2;
	cv::Mat q0(image, cv::Rect(0, 0, cx, cy));   // Top-Left - Create a ROI per quadrant
	cv::Mat q1(image, cv::Rect(cx, 0, cx, cy));  // Top-Right
	cv::Mat q2(image, cv::Rect(0, cy, cx, cy));  // Bottom-Left
	cv::Mat q3(image, cv::Rect(cx, cy, cx, cy)); // Bottom-Right

	cv::Mat tmp;                           // swap quadrants (Top-Left with Bottom-Right)
	q0.copyTo(tmp);
	q3.copyTo(q0);
	tmp.copyTo(q3);
	q1.copyTo(tmp);                    // swap quadrant (Top-Right with Bottom-Left)
	q2.copyTo(q1);
	tmp.copyTo(q2);
}
