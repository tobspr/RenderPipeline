
#include "SGRenderCallback.h"
#include "SGRenderNode.h"


TypeHandle SGRenderCallback::_type_handle;

void SGRenderCallback::do_callback(CallbackData *cbdata) {
    _render_node->do_draw_callback(cbdata, _reason);
}

SGRenderCallback::SGRenderCallback(SGRenderNode *render_node, int reason) 
    : _render_node(render_node), _reason(reason) {
}

