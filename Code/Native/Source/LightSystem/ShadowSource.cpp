#include "ShadowSource.h"


ShadowSource::ShadowSource() {
    _last_time_rendered = -1;
    _needs_update = true;
    _slot = -1;
}

ShadowSource::~ShadowSource() {

}

