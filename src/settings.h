#pragma once
#include "mode.h"
namespace pdb {
bool load_preferences(Preferences&);
bool save_preferences(Preferences);
void preferences_changed();
bool preferences_pending();
const char* preferences_status();
}
