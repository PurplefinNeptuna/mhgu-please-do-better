#pragma once
#include <stdint.h>
namespace pdb {
void install();
void request_force(bool);
bool requested_force();
bool forcing_available();
void update();
void diagnostics();
void render();
}
