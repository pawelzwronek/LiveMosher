import { MIDIInput } from "./midi.js";

import {
  get_forward_mvs,
  scaleValue,
} from "./helpers.mjs";

/*********************************************************************/
const midiin = new MIDIInput();
let midi_range_y = [ 0, 0 ];
let midi_range_x = [ 0, 0 ];

/*********************************************************************/
export function setup(args)
{
  args.features = [ "mv" ];

  midiin.setup();
  // midiin.setlog(true);
  /* faders */
  midiin.onevent ( 4, function(v) { midi_range_y[0] = v; });
  midiin.onevent ( 5, function(v) { midi_range_y[1] = v; });
  midiin.onevent ( 6, function(v) { midi_range_x[0] = v; });
  midiin.onevent ( 7, function(v) { midi_range_x[1] = v; });
}

export function glitch_frame(frame, stream)
{
  const fwd_mvs = get_forward_mvs(frame, "truncate");
  // bail out if we have no motion vectors
  if ( !fwd_mvs )
    return;

  midiin.parse_events();

  const height = 64;
  const width = 64;
  let y_begin = Math.lround(scaleValue(midi_range_y[0], 0, 127, 0, height));
  let y_end   = Math.lround(scaleValue(midi_range_y[1], 0, 127, 0, height));
  let x_begin = Math.lround(scaleValue(midi_range_x[0], 0, 127, 0, width));
  let x_end   = Math.lround(scaleValue(midi_range_x[1], 0, 127, 0, width));

  const mv_off = MV(y_end - y_begin, x_end - x_begin);
  fwd_mvs.add(mv_off);
}
