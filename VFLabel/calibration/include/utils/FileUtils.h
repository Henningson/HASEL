#pragma once

#include <string>
#include <iostream>
#include <filesystem>
#include <vector>

namespace fs = std::filesystem;

std::vector<fs::path> getFiles(std::string path, std::string file_type = ".png");