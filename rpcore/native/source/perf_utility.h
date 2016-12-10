/**
 *
 * RenderPipeline
 *
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */


#pragma once

#ifndef P3D_PERFUTILTIY_H
#define P3D_PERFUTILTIY_H

#include <vector>
#include <algorithm>
#include <cassert>

namespace performance {

  template <typename T>
  inline typename ::std::vector<T>::const_iterator vector_find(
    const ::std::vector<T>& vec, const T& elem) {
    return ::std::find(vec.cbegin(), vec.cend(), elem);
  }

  template <typename T>
  inline typename ::std::vector<T>::iterator vector_find(::std::vector<T>& vec,
                                                                  const T& elem) {
    return ::std::find(vec.begin(), vec.end(), elem);
  }

  template <typename T>
  inline bool vector_contains(const ::std::vector<T>& vec, const T& elem) {
    return ::std::find(vec.cbegin(), vec.cend(), elem) != vec.cend();
  }

  template <typename T>
  void vector_erase(::std::vector<T>& vec, typename ::std::vector<T>::iterator it) {
    assert(!vec.empty());
    auto last_element_iter = ::std::prev(vec.end());
    if (it == last_element_iter) {
      // We are removing the last element, just reduce size by 1
      vec.pop_back();
    } else {
      // We are removing any arbitrary element, swap with last element and pop
      // last
      ::std::swap(*it, *last_element_iter);
      vec.pop_back();
    }
  }

  template <typename T>
  bool vector_erase_if_contains(::std::vector<T>& vec, const T& elem) {
    // Fast removal by swapping with the last element and resizing by -1
    if (vec.empty())
      return false;
    auto it = vector_find(vec, elem);
    if (it != vec.end()) {
      vector_erase(vec, it);
      return true;
    }
    return false;
  }

  template <typename T>
  void vector_erase(::std::vector<T>& vec, const T& elem) {
    // Fast removal by swapping with the last element and resizing by -1
    // Requires: vec contains elem
    assert(!vec.empty());
    auto it = vector_find(vec, elem);
    ECS_ASSERT(it != vec.end());
    vector_erase(vec, it);
  }

  template <typename T>
  bool compare_flat_sets(const ::std::vector<T>& a, const ::std::vector<T>& b) {
    if (a.size() != b.size())
      return false;

    // O(n^2), use with care
    for (const T& elem : a) {
      if (!vector_contains(b, elem))
        return false;
    }

    return true;
  }
}

#endif