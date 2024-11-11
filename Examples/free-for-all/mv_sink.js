/*********************************************************************/
/* parameters */

// value to subtract from the vertical element of all motion vectors in
// the frame.
const value = 5;

/*********************************************************************/
class MVSink
{
  constructor(tail_length)
  {
  }

  setup(value)
  {
    this.value = value;
  }

  run(mvs)
  {
    // subtract value from the vertical element of all motion vectors
    // in the frame.
    mvs.sub_v(this.value);
  }
}

/*********************************************************************/
import {
  get_forward_mvs,
} from "./helpers.mjs";

let mv_sink;

export function setup(args)
{
  args.features = [ "mv" ];

  mv_sink = new MVSink();
  mv_sink.setup(value);
}

export function glitch_frame(frame, stream)
{
  const fwd_mvs = get_forward_mvs(frame, "truncate");
  // bail out if we have no motion vectors
  if ( !fwd_mvs )
    return;

  mv_sink.run(fwd_mvs);
}
