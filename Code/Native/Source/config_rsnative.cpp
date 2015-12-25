#include "config_rsnative.h"

#include "RPLight.h"
#include "RPPointLight.h"
#include "SGNode.h"
#include "SGRenderNode.h"
#include "SGRenderCallback.h"

#include "dconfig.h"

Configure(config_rsnative);
NotifyCategoryDef(rsnative, "");

ConfigureFn(config_rsnative) {
  init_librsnative();
}


void
init_librsnative() {
  static bool initialized = false;
  if (initialized) {
    return;
  }
  initialized = true;

  // RPLight::init_type();
  // RPPointLight::init_type();
  SGRenderCallback::init_type();
  SGNode::init_type();
  SGRenderNode::init_type();
}

