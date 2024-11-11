import { MIDIInput } from "./midi.js";

import {
  get_forward_mvs,
  scaleValue,
} from "./helpers.mjs";

const midiin = new MIDIInput();
let midi_range_y = [ 0, 0 ];
let midi_range_x = [ 0, 0 ];

const CANDIDATE_MB_TYPE_INTRA   = (1 <<  0);
const CANDIDATE_MB_TYPE_INTER   = (1 <<  1);
const CANDIDATE_MB_TYPE_INTER4V = (1 <<  2);
const CANDIDATE_MB_TYPE_INTER_I = (1 <<  8);

export function setup()
{
  midiin.setup();
  // midiin.setlog(true);
  /* faders */
  midiin.onevent ( 4, function(v) { midi_range_y[0] = v; });
  midiin.onevent ( 5, function(v) { midi_range_y[1] = v; });
  midiin.onevent ( 6, function(v) { midi_range_x[0] = v; });
  midiin.onevent ( 7, function(v) { midi_range_x[1] = v; });
}

export function mb_type_func(args)
{
  midiin.parse_events();

  const mb_types = args.mb_types;
  const mb_height = mb_types.length;
  const mb_width = mb_types[0].length;

  let y_begin = Math.lround(scaleValue(midi_range_y[0], 0, 127, 0, mb_height));
  let y_end   = Math.lround(scaleValue(midi_range_y[1], 0, 127, 0, mb_height));
  let x_begin = Math.lround(scaleValue(midi_range_x[0], 0, 127, 0, mb_width));
  let x_end   = Math.lround(scaleValue(midi_range_x[1], 0, 127, 0, mb_width));

  /* copy our global mb_types to args */
  for ( let mb_y = y_begin; mb_y < y_end; mb_y++ )
    for ( let mb_x = x_begin; mb_x < x_end; mb_x++ )
      mb_types[mb_y][mb_x] = CANDIDATE_MB_TYPE_INTRA;
}
