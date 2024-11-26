#include "utils/Timer.h"

Timer::Timer(){
	this->name = "";
}

Timer::Timer(std::string name) {
	this->name = name;
}

void Timer::start() {
	this->_start = std::chrono::steady_clock::now();
}

void Timer::stop() {
	this->count++;
	this->_duration = std::chrono::steady_clock::now() - this->_start;
	this->durations.push_back(std::chrono::duration_cast<std::chrono::milliseconds>(this->_duration).count());
	this->_sum += std::chrono::duration_cast<std::chrono::milliseconds>(this->_duration).count();
}

void Timer::printTime() {
	if (this->count == 0)
		std::cout << "Timer needs to be used once." << std::endl;

	std::cout << this->name << " " << "Duration: " << std::chrono::duration_cast<std::chrono::milliseconds>(this->_duration).count() << std::endl;
}

void Timer::printAverage() {
	if (this->count == 0)
		std::cout << "Timer needs to be used once." << std::endl;

	std::cout << this->name << " " << "Average Duration: " << this->_sum / this->count << std::endl;
}

void Timer::save() {
	std::ofstream file;
	file.open(this->name + ".txt");
	for (int duration : durations)
		file << duration << std::endl;
	file.close();
}

void Timer::saveAs(std::string filename) {
	std::ofstream file;
	file.open(filename);
	for (int duration : durations)
		file << duration << std::endl;
	file.close();
}
