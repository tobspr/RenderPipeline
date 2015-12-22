
#ifndef SHADOW_SOURCE_H
#define SHADOW_SOURCE_H




class ShadowSource {

public: 
    ShadowSource();
    ~ShadowSource();

    inline void invalidate();
    inline bool needs_update() const;

    inline int get_slot() const;
    inline void set_slot(int slot);

private:

    int _last_time_rendered;
    int _slot;
    bool _needs_update;
};



#include "ShadowSource.I"

#endif // SHADOW_SOURCE_H
