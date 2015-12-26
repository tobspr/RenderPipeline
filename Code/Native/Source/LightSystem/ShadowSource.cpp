#include "ShadowSource.h"

/**
 * @brief Constructs a new shadow source
 * @details This constructs a new shadow source, with no projection setup,
 *   and no slot assigned.
 */
ShadowSource::ShadowSource() {
    _slot = -1;
    _needs_update = true;
    _resolution = 512;
    _mvp.fill(0.0);
    _region.fill(-1);
    _region_uv.fill(0);
}
