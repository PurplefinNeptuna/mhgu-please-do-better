#pragma once
#include <stdint.h>
#include "mode.h"
namespace pdb {
void install();
const char* startup_status();
void request_force(bool);
bool requested_force();
Preferences requested_preferences();
void request_preferences(Preferences);
bool forcing_available();
void update();
void diagnostics();
void render();
}
