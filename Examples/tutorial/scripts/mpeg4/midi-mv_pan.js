import { MIDIInput } from "../../../midi.js";

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
  midiin.onevent ( 4, event => { midi_range_y[0] = event.velocity; });
  midiin.onevent ( 5, event => { midi_range_y[1] = event.velocity; });
  midiin.onevent ( 6, event => { midi_range_x[0] = event.velocity; });
  midiin.onevent ( 7, event => { midi_range_x[1] = event.velocity; });
}

export function glitch_frame(frame, stream)
{
  const fwd_mvs = frame.mv?.forward;
  // bail out if we have no forward motion vectors
  if ( !fwd_mvs )
      return;

  // set motion vector overflow behaviour in ffedit to "truncate".
  // this means that, even if we write values well beyond the
  // acceptable range, ffedit will truncate them when writing
  // back to the bitstream.
  frame.mv.overflow = "truncate";

  midiin.parse_events();

  const y_begin = midi_range_y[0];
  const y_end   = midi_range_y[1];
  const x_begin = midi_range_x[0];
  const x_end   = midi_range_x[1];

  // add pan values to all macroblocks
  const mv_off = MV(y_end - y_begin, x_end - x_begin);
  fwd_mvs.add(mv_off);
}
