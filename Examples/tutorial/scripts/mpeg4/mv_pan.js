// ./bin/fflive -i CEP00109_mpeg4.avi -s scripts/mpeg4/mv_pan.js
// ./bin/fflive -i CEP00109_mpeg4.avi -s scripts/mpeg4/mv_pan.js -sp "[ 0, 10 ]"

/*********************************************************************/
let pan_x = 1; // EXPERIMENT BY CHANGING THIS VALUE
let pan_y = 0; // EXPERIMENT BY CHANGING THIS VALUE

/*********************************************************************/
export function setup(args)
{
  // select motion vector feature
  args.features = [ "mv" ];

  // parse parameter from the command line if available
  // NOTE: the parameter from the command line should be an array with
  //       two values, like this:
  //       -sp "[ 1, 0 ]"
  // NOTE2: -sp means "script parameters"
  if ( "params" in args )
  {
    const params = args.params;
    pan_x = params[0];
    pan_y = params[1];
  }
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

  // add pan values to all macroblocks
  fwd_mvs.add(MV(pan_x, pan_y));
}
