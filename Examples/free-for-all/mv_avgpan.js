// Combination of mv_average and mv_pan
// with a toggle to switch between different glitch_frame() functions
import { MIDIInput } from "./midi_v2.js";

import {
  get_forward_mvs,
  scaleValue,
} from "./helpers.mjs";


/*********************************************************************/
const midiin = new MIDIInput();
let midi_range_y = [ 0, 0 ];
let midi_range_x = [ 0, 0 ];

const glitchFunctions = ['mv_avgpan', 'mv_average', 'mv_pan'];
let currentFunctionIndex = 0;
let activeGlitchFunction = glitchFunctions[0]

/*********************************************************************/
let tail_length = 20;
let total_sum;
let prev_mvs = [ ];
let freeze_offset = false;

/*********************************************************************/


export function setup(args)
{
  args.features = [ "mv" ];

  midiin.setup();
  midiin.setlog(true);
  /* faders */
  // Set up the event handlers for faders
midiin.onevent ( 5, function(v) { tail_length     = v.velocity; });
midiin.onevent ( 0, function(v) { midi_range_y[0] = v.velocity; });
midiin.onevent ( 1, function(v) { midi_range_y[1] = v.velocity; });
midiin.onevent ( 2, function(v) { midi_range_x[0] = v.velocity; });
midiin.onevent ( 3, function(v) { midi_range_x[1] = v.velocity; });
midiin.onbutton( 65, function(pressed) { freeze_offset = (pressed); });


/*********************************************************************/
// Hotkeys to trigger switching between glitch_frame() functions
/*********************************************************************/

// Switch glitch_frame when pressed down, change back when released
midiin.onbutton(62, function(pressed) {
  // pressed is a boolean indicating whether the note is pressed or released
  activeGlitchFunction = (activeGlitchFunction == glitchFunctions[0]) ? glitchFunctions[1] : glitchFunctions[0];
  console.log('Changed glitch_frame function to: ' + activeGlitchFunction);
});
}

// Switch between all glitch_frame() functions in the glitchFunctions array
midiin.onbutton(64, function(pressed) {
  if (pressed) { 
    // Only toggle when the button is pressed down, not when it is released
    currentFunctionIndex = (currentFunctionIndex + 1) % glitchFunctions.length;

    // Call the current glitch function
    activeGlitchFunction = glitchFunctions[currentFunctionIndex];

    // Output the name of the current function to the console
    console.log('Switched glitch_frame function to: ' + activeGlitchFunction);
  }
});


/*********************************************************************/


// Define the original glitch_frame function from mv_pan.js, renamed to mv_pan
export function mv_pan(frame, stream)
{
  const fwd_mvs = get_forward_mvs(frame, "truncate");
  // bail out if we have no motion vectors
  if ( !fwd_mvs )
    return;

  const height = 64;
  const width = 64;
  let y_begin = Math.lround(scaleValue(midi_range_y[0], 0, 127, 0, height));
  let y_end   = Math.lround(scaleValue(midi_range_y[1], 0, 127, 0, height));
  let x_begin = Math.lround(scaleValue(midi_range_x[0], 0, 127, 0, width));
  let x_end   = Math.lround(scaleValue(midi_range_x[1], 0, 127, 0, width));

  // Use MIDI values for offset if val is true
  if (freeze_offset === false) {
	  let mv_off = MV(y_end - y_begin, x_end - x_begin);
      fwd_mvs.add(mv_off);
  }
  
  // Freeze current offset if val is true
  else if (freeze_offset === true) {
	  let mv_off = new MV(0,0)
	  fwd_mvs.add(mv_off);
  }
}


// Define the original glitch_frame function from mv_average.js, renamed to mv_average
export function mv_average(frame, stream)
{
  const fwd_mvs = get_forward_mvs(frame, "truncate");
  // bail out if we have no motion vectors
  if ( !fwd_mvs )
    return;

  // update variable holding motion vectors from previous frames.
  // note that we perform a deep copy of the clean motion vector
  // values before modifying them.
  const deep_copy = fwd_mvs.dup();
  // push to the end of array
  prev_mvs.push(deep_copy);

  if ( prev_mvs.length == 1 )
  {
    // on first run, just initialize total_sum to the motion vector
    // values from the first frame.
    total_sum = deep_copy;
  }
  else
  {
    // update total_sum by removing the motion vector values from the
    // oldest frame and adding the values from the current frame.
    while ( prev_mvs.length > tail_length )
    {
      total_sum.sub(prev_mvs[0]);
      prev_mvs = prev_mvs.slice(1);
    }
    total_sum.add(deep_copy);

    // set new values for current frame to (total_sum / tail_length)
    const actual_length = prev_mvs.length;
    if ( actual_length !== 0 )
    {
      fwd_mvs.assign(total_sum);
      fwd_mvs.div(MV(actual_length,actual_length));
    }
  }
}


// Class MVAverage from mv_average.js
class MVAverage
{
  constructor()
  {
    this.prev_mvs = [];
    this.tail_length_mv = MV(tail_length, tail_length);
    this.total_sum = null;
  }

  run(mvs)
  {
    // update variable holding motion vectors from previous frames.
    const deep_copy = mvs.dup();
    this.prev_mvs.push(deep_copy);

    if (this.prev_mvs.length == 1)
    {
      this.total_sum = deep_copy;
    }
    else
    {
      if (this.prev_mvs.length > tail_length)
      {
        this.total_sum.sub(this.prev_mvs[0]);
        this.prev_mvs = this.prev_mvs.slice(1);
      }
      this.total_sum.add(deep_copy);
      mvs.assign(this.total_sum);
      mvs.div(this.tail_length_mv);
    }
  }
}
let mv_average_class = new MVAverage();

export function mv_avgpan(frame, stream)
{
  const fwd_mvs = get_forward_mvs(frame, "truncate");
  if (!fwd_mvs)
    return;

  // Apply MVAverage from mv_average.js
  mv_average_class.run(fwd_mvs);

  // Apply MIDI control from mv_pan.js
  midiin.parse_events();
  const height = 64;
  const width = 64;
  let y_begin = Math.round(scaleValue(midi_range_y[0], 0, 127, 0, height));
  let y_end   = Math.round(scaleValue(midi_range_y[1], 0, 127, 0, height));
  let x_begin = Math.round(scaleValue(midi_range_x[0], 0, 127, 0, width));
  let x_end   = Math.round(scaleValue(midi_range_x[1], 0, 127, 0, width));
  const mv_off = MV(y_end - y_begin, x_end - x_begin);
  fwd_mvs.add(mv_off);
}

/*********************************************************************/


// Define the wrapper glitch_frame function that calls the currently active function
export function glitch_frame(frame, stream) {

   midiin.parse_events();
  
  // Use eval to call the function by its name
  eval(activeGlitchFunction + '(frame, stream)');
}

/*********************************************************************/
