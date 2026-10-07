#pragma once
#include <stdint.h>
namespace pdb {
void install();
const char* startup_status();
void request_force(bool);
bool requested_force();
bool forcing_available();
void update();
void diagnostics();
void render();
}
