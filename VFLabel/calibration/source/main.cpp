#include "calibration/CameraCalibration.h"
#include "calibration/LaserCalibration.h"

#include "utils/FileUtils.h"
#include "utils/ImageUtils.h"
#include "utils/Camera.h"

#include <filesystem>
#include <vector>

#include <opencv2/core.hpp>

int main(int argc, char** argv) {

    std::cout << "Current path is " << std::filesystem::current_path() << '\n'; // (1)
    std::filesystem::current_path(std::filesystem::temp_directory_path()); // (3)
    std::cout << "Current path is " << std::filesystem::current_path() << '\n';

    std::vector<std::filesystem::path> camFiles = getFiles("/home/nu94waro/Documents/calibration/resources/calibration_data/camera/", ".png");
    std::vector<cv::Mat> camImages = IMUtils::loadImages(camFiles);

    std::vector<std::filesystem::path> laserFiles = getFiles("/home/nu94waro/Documents/calibration/resources/calibration_data/laser/", ".png");
    std::vector<cv::Mat> laserImages = IMUtils::loadImages(laserFiles);

    CameraCalibration camCalib = CameraCalibration(camImages, camFiles, 2.0);
    camCalib.calibrate();
    Camera camera = camCalib.getCamera();

    cv::Mat cameraMatrix, distortionCoefficients, originGrid, originPixel, fitGrid, fitPixel;

    Laser laserRays = Laser(18, 0.1);
    LaserCalibration laserCalib = LaserCalibration(laserImages, laserFiles, 2.0, laserRays, camera);
    laserCalib.calibrate();
    Laser optimLaser = laserCalib.getLaser();

    return -1;
}
