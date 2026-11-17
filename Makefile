# Integration tests own shared network ports and must run sequentially.
.NOTPARALLEL:
SDK := vendor/mpc-plugin-builder-sdk
CXXFLAGS := -std=c++17 -O2 -Wall -Wextra -Werror -pthread -isystem $(SDK)/framework -Isrc
SHARED := -fPIC -shared -fvisibility=hidden -fvisibility-inlines-hidden
SOURCES := src/MPCAirLink.cpp src/Receiver.cpp src/AirPlayProcess.cpp
HEADERS := src/Receiver.h src/StreamCore.h src/AirPlayProcess.h src/VbanQueue.h $(SDK)/framework/mpc_plugin.h
OUT := build/VST2 Plugins/sttm - VST - MPC AirLink
.PHONY: all arm32 arm64 test package skin sanitize airplay airplay-test
all: airplay arm32 arm64 test airplay-test package
airplay:
	./tools/build_airplay.sh
build/native/mpcairlink.so: $(SOURCES) $(HEADERS)
	mkdir -p build/native
	$(CXX) $(CXXFLAGS) $(SHARED) $(SOURCES) -o $@
build/host_sim: $(SDK)/tools/host-sim/host_sim.cpp
	mkdir -p build
	$(CXX) -std=c++17 -O2 $< -ldl -pthread -o $@
arm32: $(SOURCES) $(HEADERS)
	mkdir -p "$(OUT)/VST"
	arm-linux-gnueabihf-g++ $(CXXFLAGS) $(SHARED) -march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=hard -static-libstdc++ -static-libgcc -Wl,--no-undefined -Wl,--version-script=$(SDK)/tools/exports.map -Wl,-s $(SOURCES) -o "$(OUT)/VST/mpcairlink-arm32.so"
arm64: $(SOURCES) $(HEADERS)
	mkdir -p "$(OUT)/VST"
	aarch64-linux-gnu-g++ $(CXXFLAGS) $(SHARED) -march=armv8-a -static-libstdc++ -static-libgcc -Wl,--no-undefined -Wl,--version-script=$(SDK)/tools/exports.map -Wl,-s $(SOURCES) -o "$(OUT)/VST/mpcairlink-arm64.so"
build/core_test: tests/core_test.cpp src/StreamCore.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) $< -o $@
build/network_test: tests/network_test.cpp $(SOURCES) $(HEADERS)
	mkdir -p build
	$(CXX) $(CXXFLAGS) tests/network_test.cpp src/Receiver.cpp src/AirPlayProcess.cpp -o $@
build/jitter_test: tests/jitter_test.cpp src/StreamCore.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) $< -o $@
build/vban_queue_test: tests/vban_queue_test.cpp src/VbanQueue.h src/StreamCore.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) $< -o $@
build/vban_loss_test: tests/vban_loss_test.cpp src/Receiver.cpp src/AirPlayProcess.cpp $(HEADERS)
	mkdir -p build
	$(CXX) $(CXXFLAGS) tests/vban_loss_test.cpp src/Receiver.cpp src/AirPlayProcess.cpp -o $@
build/listening_soak: tests/listening_soak.cpp src/StreamCore.h
	mkdir -p build
	$(CXX) $(CXXFLAGS) $< -o $@
build/eco_ui_test: tests/eco_ui_test.cpp $(SOURCES) $(HEADERS)
	mkdir -p build
	$(CXX) $(CXXFLAGS) $< src/Receiver.cpp src/AirPlayProcess.cpp -o $@
test: build/native/mpcairlink.so build/host_sim build/core_test build/network_test build/jitter_test build/vban_queue_test build/vban_loss_test build/listening_soak build/eco_ui_test
	./build/core_test
	./build/jitter_test
	./build/listening_soak
	./build/vban_queue_test
	./build/vban_loss_test
	./build/network_test
	./build/eco_ui_test
	./build/host_sim build/native/mpcairlink.so dump > build/params.json
	./build/host_sim build/native/mpcairlink.so test --seconds 1 --wav build/host-test.wav > build/host-test.log 2>&1
	cat build/host-test.log
airplay-test: build/native/mpcairlink.so
	python3 tests/airplay_test.py > build/airplay-test.log 2>&1
	cat build/airplay-test.log
	python3 tests/airplay_test.py --alac > build/airplay-alac-test.log 2>&1
	cat build/airplay-alac-test.log
skin:
	python3 tools/make_skin.py
package: skin build/host_sim build/native/mpcairlink.so
	./build/host_sim build/native/mpcairlink.so dump > build/params.json
	python3 tools/package.py
sanitize:
	$(CXX) $(CXXFLAGS) -O1 -g -fsanitize=address,undefined tests/core_test.cpp -o build/core_sanitize
	./build/core_sanitize
	$(CXX) $(CXXFLAGS) -O1 -g -fsanitize=address,undefined tests/network_test.cpp src/Receiver.cpp src/AirPlayProcess.cpp -o build/network_sanitize
	./build/network_sanitize

	$(CXX) $(CXXFLAGS) -O1 -g -fsanitize=address,undefined tests/vban_queue_test.cpp -o build/vban_queue_sanitize
	./build/vban_queue_sanitize
	$(CXX) $(CXXFLAGS) -O1 -g -fsanitize=address,undefined tests/vban_loss_test.cpp src/Receiver.cpp src/AirPlayProcess.cpp -o build/vban_loss_sanitize
	./build/vban_loss_sanitize
