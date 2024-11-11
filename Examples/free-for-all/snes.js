import {
  get_forward_mvs,
} from "./helpers.mjs";

import {SDLInput} from "./sdl.js";

let sdl = new SDLInput();
let do_v = false;
let cur_off = new MV(0,0);
const step = 4;
let started = false;

export function setup(args)
{
  args.features = [ "mv" ];
  sdl.setup();
  // sdl.setlog(true);
  // X A B Y L R select start
  // 0 1 2 3 4 5 8      9
  sdl.on_button( 9, function(v) { if ( v ) started = true; });
  sdl.on_button( 1, function(v) { cur_off = new MV(0,0); });
  sdl.on_axis  ( 0, function(v) { // horizontal
    if ( v === 32767 )
      cur_off[0] -= step;
    else if ( v === -32768 )
      cur_off[0] += step;
  });
  sdl.on_axis  ( 1, function(v) { // vertical
    if ( v === 32767 )
      cur_off[1] -= step;
    else if ( v === -32768 )
      cur_off[1] += step;
  });
}

export function glitch_frame(frame, stream)
{
  let fwd_mvs = get_forward_mvs(frame, "truncate");
  // bail out if we have no motion vectors
  if ( !fwd_mvs )
    return;

  // parse SDL events
  sdl.parse_events();

  if ( started )
    fwd_mvs.add(cur_off);
}
