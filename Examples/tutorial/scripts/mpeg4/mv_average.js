// ./bin/fflive -i CEP00109_mpeg4.avi -s scripts/mpeg4/mv_average.js

/*********************************************************************/
// experiment with this value to use a smaller or greater number of
// frames to perform the average of motion vectors
const tail_length = 10;

/*********************************************************************/
// global variable holding forward motion vectors from previous frames
let prev_fwd_mvs = [ ];
let total_sum;

export function setup(args)
{
  // select motion vector feature
  args.features = [ "mv" ];
}

export function glitch_frame(frame)
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

  // update variable holding forward motion vectors from previous
  // frames. note that we perform a deep copy of the clean motion
  // vector values before modifying them.
  const deep_copy = fwd_mvs.dup();
  // push to the end of array
  prev_fwd_mvs.push(deep_copy);

  // initialize total_sum to a [0,0] MV2DArray.
  if ( !total_sum )
      total_sum = new MV2DArray(fwd_mvs.width, fwd_mvs.height);

  // update total_sum by removing the motion vector values from the
  // oldest frame and adding the values from the current frame.
  if ( prev_fwd_mvs.length > tail_length )
  {
    total_sum.sub(prev_fwd_mvs[0]);
    prev_fwd_mvs = prev_fwd_mvs.slice(1);
  }
  total_sum.add(deep_copy);

  // set new values for current frame to (total_sum / tail_length)
  if ( prev_fwd_mvs.length == tail_length )
  {
    fwd_mvs.assign(total_sum);
    fwd_mvs.div(MV(tail_length, tail_length));
  }
}
