import { MIDIInput } from "./midi.js";

import {
  scaleValue
} from "./helpers.mjs";

const midiin = new MIDIInput();
let midi_range_y = [ 0, 0 ];
let midi_range_x = [ 0, 0 ];
let midi_threshold_low = 0.25;
let midi_threshold_high = 0.80;
let midi_clength = 0;
let midi_order = 0;
let midi_trigger_by = 0;
let midi_sort_by = 0;
let midi_mode = 0;

export function setup(args)
{
  args.pix_fmt = "gbrp";

  midiin.setup();
  // midiin.setlog(true);
  /* faders */
  midiin.onevent ( 0, function(v) { midi_range_y[0] = v; });
  midiin.onevent ( 1, function(v) { midi_range_y[1] = v; });
  midiin.onevent ( 2, function(v) { midi_range_x[0] = v; });
  midiin.onevent ( 3, function(v) { midi_range_x[1] = v; });
  midiin.onevent ( 4, function(v) { midi_mode = 0; midi_threshold_low = v; });
  midiin.onevent ( 5, function(v) { midi_mode = 0; midi_threshold_high = v; });
  midiin.onevent ( 6, function(v) { midi_mode = 1; midi_clength = v; });
  /* buttons */
  // set vertical
  midiin.onbutton(32, function(v) { if ( v ) midi_order = 0; });
  midiin.onbutton(48, function(v) { if ( v ) midi_order = 0; });
  midiin.onbutton(64, function(v) { if ( v ) midi_order = 0; });
  midiin.onbutton(33, function(v) { if ( v ) midi_order = 0; });
  midiin.onbutton(49, function(v) { if ( v ) midi_order = 0; });
  midiin.onbutton(65, function(v) { if ( v ) midi_order = 0; });
  // set horizontal
  midiin.onbutton(34, function(v) { if ( v ) midi_order = 1; });
  midiin.onbutton(50, function(v) { if ( v ) midi_order = 1; });
  midiin.onbutton(66, function(v) { if ( v ) midi_order = 1; });
  midiin.onbutton(35, function(v) { if ( v ) midi_order = 1; });
  midiin.onbutton(51, function(v) { if ( v ) midi_order = 1; });
  midiin.onbutton(67, function(v) { if ( v ) midi_order = 1; });
  // trigger_by
  midiin.onbutton(36, function(v) { if ( v ) midi_trigger_by = 0; });
  midiin.onbutton(52, function(v) { if ( v ) midi_trigger_by = 1; });
  midiin.onbutton(68, function(v) { if ( v ) midi_trigger_by = 2; });
  // sort_by
  midiin.onbutton(37, function(v) { if ( v ) midi_sort_by = 0; });
  midiin.onbutton(53, function(v) { if ( v ) midi_sort_by = 1; });
  midiin.onbutton(69, function(v) { if ( v ) midi_sort_by = 2; });
}

let first_frame = true;
export function filter(args)
{
  let data = args["data"];
  const height = data[0].height;
  const width  = data[0].width;

  midiin.parse_events();

  if ( first_frame == true )
  {
    // set default options
    midi_mode = 0;
    midi_order = 0;
    midi_trigger_by = 2;
    midi_sort_by = 2;
    first_frame = false;
  }

  let options = {
    pix_fmt: "hsl",             // rgb, hsv, hsl
    trigger_by: "l",
    sort_by: "l",
    order: "horizontal",
    mode: "threshold",
    reverse_sort: false,
    threshold: [ 0.25, 0.80 ],  // can be high low or low high
    clength: 100,
  };

  if ( midi_mode === 0 )
    options.mode = "threshold";
  else
    options.mode = "random";

  let y_begin = Math.lround(scaleValue(midi_range_y[0], 0, 127, 0, height));
  let y_end   = Math.lround(scaleValue(midi_range_y[1], 0, 127, 0, height));
  let x_begin = Math.lround(scaleValue(midi_range_x[0], 0, 127, 0, width));
  let x_end   = Math.lround(scaleValue(midi_range_x[1], 0, 127, 0, width));
  let threshold_low = scaleValue(midi_threshold_low, 0, 127, 0, 1);
  let threshold_high = scaleValue(midi_threshold_high, 0, 127, 0, 1);

  const swapped_y = (y_begin > y_end);
  const swapped_x = (x_begin > x_end);

  let reverse_sort = false;
  if ( (swapped_y && !midi_order)
    || (swapped_x && midi_order) )
  {
    reverse_sort = true;
  }
  if ( swapped_y )
  {
    const tmp = y_begin;
    y_begin = y_end;
    y_end = tmp;
  }
  if ( swapped_x )
  {
    const tmp = x_begin;
    x_begin = x_end;
    x_end = tmp;
  }

  if ( midi_order === 0 )
  {
    options.order = "vertical";
    options.clength = Math.lround(scaleValue(midi_clength, 0, 127, 0, (x_end - x_begin)));
  }
  else
  {
    options.order = "horizontal";
    options.clength = Math.lround(scaleValue(midi_clength, 0, 127, 0, (y_end - y_begin)));
  }

  if ( y_begin != y_end && y_end !== 0 && y_begin !== height
    && x_begin != x_end && x_end !== 0 && x_begin !== width )
  {
    // update options
    options.reverse_sort = reverse_sort;
    options.threshold = [ threshold_low, threshold_high ];
    options.trigger_by = options.pix_fmt[midi_trigger_by];
    options.sort_by = options.pix_fmt[midi_sort_by];

    const range_y = [ y_begin, y_end ];
    const range_x = [ x_begin, x_end ];

    // pixelsort(data, [ range y ], [ range x ], options)
    ffgac.pixelsort(data, range_y, range_x, options);
  }
}
