#include "ShadowSource.h"


ShadowSource::ShadowSource() {
    _needs_update = true;
    _slot = -1;
    _resolution = 512;
    _region.set(-1, -1, -1, -1);
    _region_uv.set(0, 0, 0, 0);
}

ShadowSource::~ShadowSource() {

}

