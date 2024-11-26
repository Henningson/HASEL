#include "utils/FileUtils.h"

std::vector<std::filesystem::path> getFiles(std::string path, std::string file_type) {
	std::vector<fs::path> paths;
	for (const auto& entry : fs::directory_iterator(path)) {
		auto bla = entry.path().extension();
		if (entry.path().extension() == file_type)
			paths.push_back(entry.path());
	}
	return paths;
}
