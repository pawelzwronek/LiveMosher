import { MIDIInput } from "../../midi.js";

import {
  scaleValue
} from "../helpers.mjs";

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
  midiin.onevent ( 0, event => { midi_range_y[0] = event.velocity; });
  midiin.onevent ( 1, event => { midi_range_y[1] = event.velocity; });
  midiin.onevent ( 2, event => { midi_range_x[0] = event.velocity; });
  midiin.onevent ( 3, event => { midi_range_x[1] = event.velocity; });
  midiin.onevent ( 4, event => { midi_mode = 0; midi_threshold_low = event.velocity; });
  midiin.onevent ( 5, event => { midi_mode = 0; midi_threshold_high = event.velocity; });
  midiin.onevent ( 6, event => { midi_mode = 1; midi_clength = event.velocity; });
  /* buttons */
  // set vertical
  midiin.onbutton(32, pressed => { if (pressed) midi_order = 0; });
  midiin.onbutton(48, pressed => { if (pressed) midi_order = 0; });
  midiin.onbutton(64, pressed => { if (pressed) midi_order = 0; });
  midiin.onbutton(33, pressed => { if (pressed) midi_order = 0; });
  midiin.onbutton(49, pressed => { if (pressed) midi_order = 0; });
  midiin.onbutton(65, pressed => { if (pressed) midi_order = 0; });
  // set horizontal
  midiin.onbutton(34, pressed => { if (pressed) midi_order = 1; });
  midiin.onbutton(50, pressed => { if (pressed) midi_order = 1; });
  midiin.onbutton(66, pressed => { if (pressed) midi_order = 1; });
  midiin.onbutton(35, pressed => { if (pressed) midi_order = 1; });
  midiin.onbutton(51, pressed => { if (pressed) midi_order = 1; });
  midiin.onbutton(67, pressed => { if (pressed) midi_order = 1; });
  // trigger_by
  midiin.onbutton(36, pressed => { if (pressed) midi_trigger_by = 0; });
  midiin.onbutton(52, pressed => { if (pressed) midi_trigger_by = 1; });
  midiin.onbutton(68, pressed => { if (pressed) midi_trigger_by = 2; });
  // sort_by
  midiin.onbutton(37, pressed => { if (pressed) midi_sort_by = 0; });
  midiin.onbutton(53, pressed => { if (pressed) midi_sort_by = 1; });
  midiin.onbutton(69, pressed => { if (pressed) midi_sort_by = 2; });
}

let first_frame = true;
export function filter(args)
{
  const data = args["data"];
  const height = data[0].height;
  const width  = data[0].width;

  midiin.parse_events();

  if ( first_frame == true )
  {
    // set default options
    midi_mode = 0;
    midi_order = 1;
    midi_trigger_by = 2;
    midi_sort_by = 2;
    first_frame = false;
  }

  const options = {
    colorspace: "hsl",             // rgb, hsv, hsl
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
    options.trigger_by = options.colorspace[midi_trigger_by];
    options.sort_by = options.colorspace[midi_sort_by];

    const range_y = [ y_begin, y_end ];
    const range_x = [ x_begin, x_end ];

    // pixelsort(data, [ range y ], [ range x ], options)
    ffgac.pixelsort(data, range_y, range_x, options);
  }
}
