// Filename: perlinNoise2.h
// Created by:  drose (05Oct05)
//
////////////////////////////////////////////////////////////////////
//
// PANDA 3D SOFTWARE
// Copyright (c) 2001 - 2004, Disney Enterprises, Inc.  All rights reserved
//
// All use of this software is subject to the terms of the Panda 3d
// Software license.  You should have received a copy of this license
// along with this source code; you will also find a current copy of
// the license at http://etc.cmu.edu/panda3d/docs/license/ .
//
// To contact the maintainers of this program write to
// panda3d-general@lists.sourceforge.net .
//
////////////////////////////////////////////////////////////////////

#ifndef PERLINNOISE2_H
#define PERLINNOISE2_H

#include "pandabase.h"
#include "perlinNoise.h"

////////////////////////////////////////////////////////////////////
//       Class : PerlinNoise2
// Description : This class provides an implementation of Perlin noise
//               for 2 variables.  This code is loosely based on the
//               reference implementation at
//               http://mrl.nyu.edu/~perlin/noise/ .
////////////////////////////////////////////////////////////////////
class EXPCL_PANDA PerlinNoise2 : public PerlinNoise {
PUBLISHED:
  INLINE PerlinNoise2();
  INLINE PerlinNoise2(double sx, double sy,
		      int table_size = 256,
		      unsigned long seed = 0);
  INLINE PerlinNoise2(const PerlinNoise2 &copy);
  INLINE void operator = (const PerlinNoise2 &copy);

  INLINE void set_scale(double scale);
  INLINE void set_scale(double sx, double sy);
  INLINE void set_scale(const LVecBase2f &scale);
  void set_scale(const LVecBase2d &scale);

  INLINE double noise(double x, double y) const;
  INLINE float noise(const LVecBase2f &value) const;
  double noise(const LVecBase2d &value) const;

  INLINE double operator ()(double x, double y) const;
  INLINE float operator ()(const LVecBase2f &value) const;
  INLINE double operator ()(const LVecBase2d &value) const;
  
private:
  void init_unscaled_xform();
  INLINE static double grad(int hash, double x, double y);

private:
  LMatrix3d _unscaled_xform;
  LMatrix3d _input_xform;
};

#include "perlinNoise2.I"

#endif

