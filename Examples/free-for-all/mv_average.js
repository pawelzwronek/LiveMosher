/*********************************************************************/
/* parameters */

// change this value to use a smaller or greater number of frames to
// perform the average of motion vectors
const tail_length = 3;

/*********************************************************************/
class MVAverage
{
  constructor()
  {
    this.prev_mvs = [ ];
  }

  setup(tail_length)
  {
    this.tail_length_mv = MV(tail_length,tail_length);
  }

  run(mvs)
  {
    // update variable holding motion vectors from previous frames.
    // note that we perform a deep copy of the clean motion vector
    // values before modifying them.
    const deep_copy = mvs.dup();
    // push to the end of array
    this.prev_mvs.push(deep_copy);

    if ( this.prev_mvs.length == 1 )
    {
      // on first run, just initialize total_sum to the motion vector
      // values from the first frame.
      this.total_sum = deep_copy;
    }
    else
    {
      // update total_sum by removing the motion vector values from the
      // oldest frame and adding the values from the current frame.
      if ( this.prev_mvs.length > tail_length )
      {
        this.total_sum.sub(this.prev_mvs[0]);
        this.prev_mvs = this.prev_mvs.slice(1);
      }
      this.total_sum.add(deep_copy);

      // set new values for current frame to (total_sum / tail_length)
      mvs.assign(this.total_sum);
      mvs.div(this.tail_length_mv);
    }
  }
}

/*********************************************************************/
import {
  get_forward_mvs,
} from "./helpers.mjs";

let mv_average;

export function setup(args)
{
  args.features = [ "mv" ];

  mv_average = new MVAverage();
  mv_average.setup(tail_length);
}

export function glitch_frame(frame, stream)
{
  const fwd_mvs = get_forward_mvs(frame, "truncate");
  // bail out if we have no motion vectors
  if ( !fwd_mvs )
    return;

  mv_average.run(fwd_mvs);
}
