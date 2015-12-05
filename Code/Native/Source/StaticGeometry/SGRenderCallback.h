
#pragma once

#include "pandabase.h"
#include "callbackObject.h"
#include "typeHandle.h"

class SGRenderNode;

class SGRenderCallback : public CallbackObject {
public:
  SGRenderCallback(SGRenderNode *render_node, int reason);
  ALLOC_DELETED_CHAIN(SGRenderCallback);

public:
  virtual void do_callback(CallbackData *cbdata);

private:
  SGRenderNode *_render_node;
  int _reason;

public:
  static TypeHandle get_class_type() {
    return _type_handle;
  }
  static void init_type() {
    CallbackObject::init_type();
    register_type(_type_handle, "SGRenderCallback",
                  CallbackObject::get_class_type());
  }
  virtual TypeHandle get_type() const {
    return get_class_type();
  }
  virtual TypeHandle force_init_type() {init_type(); return get_class_type();}

private:
  static TypeHandle _type_handle;
};
