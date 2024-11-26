#pragma once

#include <chrono>
#include <iostream>
#include <vector>
#include <fstream>

class Timer {
public:
	Timer();
	Timer(std::string name);
	void start();
	void stop();

	void printTime();
	void printAverage();
	void saveAs(std::string filename);
	void save();

protected:
	std::string name;
	std::vector<int> durations;
	int count = 0;
	std::chrono::steady_clock::time_point _start;
	std::chrono::steady_clock::duration _duration;
	int _sum = 0;
};