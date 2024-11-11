import { MIDIInput } from "./midi.js";

import {
  get_forward_mvs,
  scaleValue,
} from "./helpers.mjs";

/*********************************************************************/
const midiin = new MIDIInput();
let tail_length = 20;

/*********************************************************************/
let total_sum;
let prev_mvs = [ ];

/*********************************************************************/
export function setup(args)
{
  args.features = [ "mv" ];
  midiin.setup();
  // midiin.setlog(true);
  /* faders */
  midiin.onevent ( 4, function(v) { tail_length = v; });
}

export function glitch_frame(frame, stream)
{
  const fwd_mvs = get_forward_mvs(frame, "truncate");
  // bail out if we have no motion vectors
  if ( !fwd_mvs )
    return;

  midiin.parse_events();

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
